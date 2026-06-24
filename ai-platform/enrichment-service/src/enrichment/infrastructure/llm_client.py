"""Multi-provider LLM client with retry, cost tracking, and structured output.

Cloud AI First - uses unified CloudLLMClient with provider fallback.
Gemini (primary for Indonesian) → Claude (secondary for quality) → OpenAI (fallback).
All via cloud APIs. No local/self-hosted models.
"""

import os
import json
import time
import structlog
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import the new unified cloud LLM client
from ai_shared.llm.cloud_llm_client import (
    CloudLLMClient,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)

logger = structlog.get_logger(__name__)


# Re-export LLMProvider from the new module for compatibility
LLMProvider = LLMProvider  # Uses the enum from cloud_llm_client


class LLMError(Exception):
    """Base exception for LLM API errors."""
    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM API rate limit is exceeded."""
    pass


class LLMContextWindowExceededError(LLMError):
    """Raised when input exceeds model's context window."""
    pass


@dataclass
class LLMUsage:
    """Token usage and cost tracking for LLM calls."""
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    duration_ms: float = 0.0
    model_name: str = ""
    provider: str = ""


# Cost per 1M tokens (as of June 2026)
MODEL_COSTS = {
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for an LLM call based on token usage."""
    costs = MODEL_COSTS.get(model, {"input": 0.0, "output": 0.0})
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return round(input_cost + output_cost, 8)


class LLMClient(ABC):
    """Abstract base for LLM providers with structured JSON output."""

    @abstractmethod
    async def extract_structured(
        self, prompt: str, response_schema: dict, max_tokens: int = 4096
    ) -> tuple[dict, LLMUsage]:
        ...

    @abstractmethod
    def get_context_window(self) -> int:
        ...


class GeminiClient(LLMClient):
    """Google Gemini client with structured JSON mode.

    Primary LLM for enrichment. 1M token context window.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-1.5-flash"):
        import google.generativeai as genai
        genai.configure(api_key=api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)
        self.provider = "gemini"
        self.model_name = model
        self.context_window = 1_000_000 if "flash" in model else 200_000
        logger.info("gemini_client_initialized", model=model, context_window=self.context_window)

    def get_context_window(self) -> int:
        return self.context_window

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((LLMRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def extract_structured(
        self, prompt: str, response_schema: dict, max_tokens: int = 4096
    ) -> tuple[dict, LLMUsage]:
        """Extract structured data using Gemini with JSON mode.

        Returns:
            Tuple of (parsed_result, LLMUsage)
        """
        import google.generativeai as genai
        start = time.time()

        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.2,
                    max_output_tokens=max_tokens,
                ),
            )

            duration_ms = (time.time() - start) * 1000

            # Estimate token usage from response
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count or 0
                output_tokens = response.usage_metadata.candidates_token_count or 0
            else:
                # Estimate: ~4 chars per token
                input_tokens = len(prompt) // 4
                output_tokens = len(str(response.text)) // 4

            cost = calculate_cost(self.model_name, input_tokens, output_tokens)

            usage = LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                duration_ms=round(duration_ms, 2),
                model_name=self.model_name,
                provider=self.provider,
            )

            result = response.parsed if hasattr(response, 'parsed') and response.parsed else json.loads(response.text)

            logger.info(
                "gemini_extraction_completed",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                duration_ms=round(duration_ms, 2),
            )

            return result, usage

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str or "quota" in error_str:
                raise LLMRateLimitError(f"Gemini rate limited: {e}")
            if "context" in error_str and "length" in error_str:
                raise LLMContextWindowExceededError(f"Gemini context window exceeded: {e}")
            raise LLMError(f"Gemini extraction failed: {e}")


class ClaudeClient(LLMClient):
    """Anthropic Claude client with JSON mode.

    Secondary LLM for enrichment. Better for complex structured extraction.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.model = model
        self.provider = "claude"
        self.model_name = model
        self.context_window = 200_000
        logger.info("claude_client_initialized", model=model)

    def get_context_window(self) -> int:
        return self.context_window

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((LLMRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def extract_structured(
        self, prompt: str, response_schema: dict, max_tokens: int = 4096
    ) -> tuple[dict, LLMUsage]:
        """Extract structured data using Claude with JSON mode.

        Returns:
            Tuple of (parsed_result, LLMUsage)
        """
        start = time.time()

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )

            duration_ms = (time.time() - start) * 1000

            # Parse token usage
            input_tokens = response.usage.input_tokens if hasattr(response.usage, 'input_tokens') else 0
            output_tokens = response.usage.output_tokens if hasattr(response.usage, 'output_tokens') else 0

            cost = calculate_cost(self.model_name, input_tokens, output_tokens)

            usage = LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                duration_ms=round(duration_ms, 2),
                model_name=self.model_name,
                provider=self.provider,
            )

            result = json.loads(response.content[0].text)

            logger.info(
                "claude_extraction_completed",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                duration_ms=round(duration_ms, 2),
            )

            return result, usage

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str:
                raise LLMRateLimitError(f"Claude rate limited: {e}")
            if "too large" in error_str or "context" in error_str:
                raise LLMContextWindowExceededError(f"Claude context window exceeded: {e}")
            raise LLMError(f"Claude extraction failed: {e}")


class OpenAIClient(LLMClient):
    """OpenAI client with JSON mode.

    Fallback LLM for enrichment.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.provider = "openai"
        self.model_name = model
        self.context_window = 128_000
        logger.info("openai_client_initialized", model=model)

    def get_context_window(self) -> int:
        return self.context_window

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((LLMRateLimitError, ConnectionError)),
        reraise=True,
    )
    async def extract_structured(
        self, prompt: str, response_schema: dict, max_tokens: int = 4096
    ) -> tuple[dict, LLMUsage]:
        """Extract structured data using OpenAI with JSON mode.

        Returns:
            Tuple of (parsed_result, LLMUsage)
        """
        start = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=max_tokens,
            )

            duration_ms = (time.time() - start) * 1000

            # Parse token usage
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens or 0
                output_tokens = response.usage.completion_tokens or 0
            else:
                input_tokens = len(prompt) // 4
                output_tokens = len(str(response.choices[0].message.content)) // 4

            cost = calculate_cost(self.model_name, input_tokens, output_tokens)

            usage = LLMUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
                duration_ms=round(duration_ms, 2),
                model_name=self.model_name,
                provider=self.provider,
            )

            result = json.loads(response.choices[0].message.content)

            logger.info(
                "openai_extraction_completed",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost=cost,
                duration_ms=round(duration_ms, 2),
            )

            return result, usage

        except Exception as e:
            error_str = str(e).lower()
            if "rate" in error_str:
                raise LLMRateLimitError(f"OpenAI rate limited: {e}")
            if "context" in error_str or "length" in error_str:
                raise LLMContextWindowExceededError(f"OpenAI context window exceeded: {e}")
            raise LLMError(f"OpenAI extraction failed: {e}")


class LLMClientRouter:
    """Router that tries LLM providers in order with fallback.

    Routing strategy (from PRD v2.0):
    - Transcript < 100K tokens: Gemini Flash → Claude Haiku → GPT-4o Mini
    - Transcript 100K–800K tokens: Gemini Flash → Gemini Pro → Claude (chunked)
    - Transcript > 800K tokens: Chunked Gemini Flash
    """

    def __init__(self):
        self.clients = {
            "gemini_flash": None,
            "gemini_pro": None,
            "claude_sonnet": None,
            "claude_haiku": None,
            "gpt4o": None,
            "gpt4o_mini": None,
        }
        self._init_clients()

    def _init_clients(self):
        """Initialize LLM clients."""
        try:
            self.clients["gemini_flash"] = GeminiClient(model="gemini-1.5-flash")
        except Exception as e:
            logger.warning("gemini_flash_unavailable", error=str(e))

        try:
            self.clients["gemini_pro"] = GeminiClient(model="gemini-1.5-pro")
        except Exception as e:
            logger.warning("gemini_pro_unavailable", error=str(e))

        try:
            self.clients["claude_sonnet"] = ClaudeClient(model="claude-3-5-sonnet-20241022")
        except Exception as e:
            logger.warning("claude_sonnet_unavailable", error=str(e))

        try:
            self.clients["claude_haiku"] = ClaudeClient(model="claude-3-5-haiku-20241022")
        except Exception as e:
            logger.warning("claude_haiku_unavailable", error=str(e))

        try:
            self.clients["gpt4o"] = OpenAIClient(model="gpt-4o")
        except Exception as e:
            logger.warning("gpt4o_unavailable", error=str(e))

        try:
            self.clients["gpt4o_mini"] = OpenAIClient(model="gpt-4o-mini")
        except Exception as e:
            logger.warning("gpt4o_mini_unavailable", error=str(e))

    def get_chain_for_transcript(self, transcript_length: int) -> list[LLMClient]:
        """Get ordered list of LLM clients based on transcript length.

        Args:
            transcript_length: Number of tokens in the transcript

        Returns:
            Ordered list of LLM clients to try
        """
        if transcript_length < 100_000:
            return [
                self.clients["gemini_flash"],
                self.clients["claude_haiku"],
                self.clients["gpt4o_mini"],
            ]
        elif transcript_length < 800_000:
            return [
                self.clients["gemini_flash"],
                self.clients["gemini_pro"],
                self.clients["claude_sonnet"],
            ]
        else:
            # > 800K tokens — need chunking
            return [self.clients["gemini_flash"]]

    async def extract_structured(
        self,
        prompt: str,
        response_schema: dict,
        transcript_length: int = 0,
        max_tokens: int = 4096,
    ) -> tuple[dict, LLMUsage]:
        """Try each LLM client in order until one succeeds.

        Args:
            prompt: The prompt to send
            response_schema: JSON schema for structured output
            transcript_length: Token count for routing decision
            max_tokens: Maximum output tokens

        Returns:
            Tuple of (parsed_result, LLMUsage)

        Raises:
            LLMError: If all providers fail
        """
        chain = self.get_chain_for_transcript(transcript_length)
        chain = [c for c in chain if c is not None]

        if not chain:
            raise LLMError("No LLM clients available")

        last_error = None
        for client in chain:
            try:
                result, usage = await client.extract_structured(prompt, response_schema, max_tokens)
                logger.info(
                    "llm_extraction_succeeded",
                    provider=client.provider,
                    model=client.model_name,
                    cost=usage.cost_usd,
                )
                return result, usage
            except LLMContextWindowExceededError as e:
                logger.warning("llm_context_exceeded_try_next", provider=client.provider, error=str(e))
                last_error = e
                continue
            except LLMRateLimitError as e:
                logger.warning("llm_rate_limited_try_next", provider=client.provider, error=str(e))
                last_error = e
                continue
            except LLMError as e:
                logger.warning("llm_failed_try_next", provider=client.provider, error=str(e))
                last_error = e
                continue

        raise LLMError(f"All LLM providers failed. Last error: {last_error}")


def create_llm_client(provider: str = "gemini") -> LLMClient:
    """Factory: create single LLM client based on provider name.
    
    DEPRECATED: Use CloudLLMClientAdapter for new code.
    This factory is kept for backward compatibility.
    """
    provider = provider or os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider == "claude":
        return ClaudeClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        return GeminiClient()


class CloudLLMClientAdapter(LLMClient):
    """Adapter to use unified CloudLLMClient for structured extraction.
    
    This adapter wraps the new CloudLLMClient (from ai_shared.llm.cloud_llm_client)
    to provide the same interface as the legacy LLMClient, but with improved
    provider fallback, rate limiting, and cost tracking.
    
    Recommended for all new enrichment code.
    """

    def __init__(
        self,
        primary_provider: LLMProvider = LLMProvider.GEMINI,
        fallback_providers: Optional[list[LLMProvider]] = None,
        rate_limit_rpm: int = 60,
    ):
        """Initialize the adapter with a CloudLLMClient instance.
        
        Args:
            primary_provider: Primary cloud provider (default: Gemini for Indonesian)
            fallback_providers: List of fallback providers
            rate_limit_rpm: Rate limit per minute for each provider
        """
        self.cloud_client = CloudLLMClient(
            primary_provider=primary_provider,
            fallback_providers=fallback_providers,
            rate_limit_rpm=rate_limit_rpm,
        )
        self.provider = primary_provider.value
        self.model_name = self.cloud_client.DEFAULT_MODELS[primary_provider]
        self.context_window = 1_000_000  # Gemini Flash has 1M context
        
        logger.info(
            "cloud_llm_adapter_initialized",
            primary=primary_provider.value,
            model=self.model_name,
        )

    def get_context_window(self) -> int:
        """Return the context window size."""
        return self.context_window

    async def extract_structured(
        self,
        prompt: str,
        response_schema: dict,
        max_tokens: int = 4096,
    ) -> tuple[dict, LLMUsage]:
        """Extract structured data using cloud LLM with JSON mode.
        
        Args:
            prompt: The prompt with schema instructions
            response_schema: JSON schema for expected output
            max_tokens: Maximum output tokens
            
        Returns:
            Tuple of (parsed_result, LLMUsage)
        """
        # Add JSON mode instructions to the prompt
        json_instruction = f"""
Respond with valid JSON that matches this schema:
{json.dumps(response_schema, indent=2)}

Ensure your response is ONLY valid JSON, no additional text.
"""
        full_prompt = f"{prompt}\n\n{json_instruction}"
        
        request = LLMRequest(
            prompt=full_prompt,
            temperature=0.2,
            max_tokens=max_tokens,
        )
        
        response = await self.cloud_client.generate(request)
        
        # Parse JSON from response
        try:
            result = json.loads(response.text)
        except json.JSONDecodeError:
            # Try to extract JSON from response if there's extra text
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                logger.error("failed_to_parse_json", response=response.text[:200])
                raise LLMError(f"Failed to parse JSON from response: {response.text[:200]}")
        
        # Convert LLMResponse to LLMUsage for compatibility
        usage = LLMUsage(
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost_usd=response.cost_usd,
            duration_ms=response.latency_seconds * 1000,
            model_name=response.model,
            provider=response.provider.value,
        )
        
        logger.info(
            "cloud_llm_extraction_completed",
            provider=response.provider.value,
            model=response.model,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            cost=usage.cost_usd,
            duration_ms=usage.duration_ms,
        )
        
        return result, usage

    async def close(self):
        """Close the underlying cloud client."""
        await self.cloud_client.close()


def create_cloud_llm_client(
    primary_provider: str = "gemini",
    fallback_providers: Optional[list[str]] = None,
    rate_limit_rpm: int = 60,
) -> CloudLLMClientAdapter:
    """Factory: create CloudLLMClientAdapter for structured extraction.
    
    This is the recommended factory for new code.
    
    Args:
        primary_provider: Primary provider (gemini, claude, openai)
        fallback_providers: List of fallback providers
        rate_limit_rpm: Rate limit per minute
        
    Returns:
        CloudLLMClientAdapter instance
    """
    primary = LLMProvider(primary_provider)
    fallbacks = [LLMProvider(p) for p in (fallback_providers or [])]
    
    return CloudLLMClientAdapter(
        primary_provider=primary,
        fallback_providers=fallbacks,
        rate_limit_rpm=rate_limit_rpm,
    )