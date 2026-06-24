"""Unified Cloud LLM Client with Provider Fallback.

Supports multiple cloud AI providers (OpenAI, Claude, Gemini) with
automatic fallback, rate limiting, and cost tracking.

Removes all self-hosted model options (Llama, Mistral, etc.) in favor
of cloud APIs for reliability and cost optimization.
"""

import os
import asyncio
import structlog
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

try:
    from anthropic import AsyncAnthropic
except ImportError:
    AsyncAnthropic = None

try:
    import google.genai as genai
except ImportError:
    genai = None

logger = structlog.get_logger(__name__)


class LLMProvider(str, Enum):
    """Cloud AI providers."""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"


@dataclass
class LLMRequest:
    """LLM request parameters."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    provider: Optional[LLMProvider] = None
    model: Optional[str] = None


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    text: str
    provider: LLMProvider
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_seconds: float
    timestamp: datetime


class RateLimiter:
    """Simple token bucket rate limiter per provider."""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.tokens = requests_per_minute
        self.last_refill = datetime.now()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token from the bucket."""
        async with self.lock:
            now = datetime.now()
            elapsed = (now - self.last_refill).total_seconds()
            
            # Refill tokens
            self.tokens = min(
                self.requests_per_minute,
                self.tokens + elapsed * (self.requests_per_minute / 60)
            )
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / (self.requests_per_minute / 60)
                logger.info("rate_limit_wait", wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
                self.tokens = 1
            else:
                self.tokens -= 1


class CloudLLMClient:
    """Unified cloud LLM client with provider fallback.
    
    Removes self-hosted options, supports OpenAI, Claude, and Gemini.
    Implements rate limiting, cost tracking, and automatic fallback.
    """

    # Cost per 1K tokens (as of 2025)
    COST_PER_1K = {
        # OpenAI
        LLMProvider.OPENAI: {
            "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
            "gpt-4o": {"input": 0.00250, "output": 0.01000},
            "gpt-4o-2024-08-06": {"input": 0.00250, "output": 0.01000},
        },
        # Claude
        LLMProvider.CLAUDE: {
            "claude-3-5-sonnet-20241022": {"input": 0.00300, "output": 0.01500},
            "claude-3-5-haiku-20241022": {"input": 0.00080, "output": 0.00400},
        },
        # Gemini
        LLMProvider.GEMINI: {
            "gemini-2.5-flash": {"input": 0.000075, "output": 0.00030},
            "gemini-2.0-flash": {"input": 0.000075, "output": 0.00030},
        },
    }

    # Default models
    DEFAULT_MODELS = {
        LLMProvider.OPENAI: "gpt-4o-mini",
        LLMProvider.CLAUDE: "claude-3-5-haiku-20241022",
        LLMProvider.GEMINI: "gemini-2.5-flash",
    }

    def __init__(
        self,
        primary_provider: LLMProvider = LLMProvider.GEMINI,  # Optimized for Indonesian
        fallback_providers: Optional[List[LLMProvider]] = None,
        rate_limit_rpm: int = 60,
    ):
        self.primary_provider = primary_provider
        self.fallback_providers = fallback_providers or [
            LLMProvider.OPENAI,
            LLMProvider.CLAUDE,
        ]
        self.rate_limit_rpm = rate_limit_rpm
        
        # Initialize rate limiters
        self.rate_limiters = {
            provider: RateLimiter(rate_limit_rpm)
            for provider in LLMProvider
        }
        
        # Initialize clients
        self.clients: Dict[LLMProvider, Any] = {}
        self._init_clients()
        
        logger.info(
            "cloud_llm_client_initialized",
            primary=primary_provider.value,
            fallbacks=[p.value for p in self.fallback_providers],
        )

    def _init_clients(self):
        """Initialize API clients for all providers."""
        # OpenAI
        if AsyncOpenAI and os.getenv("OPENAI_API_KEY"):
            self.clients[LLMProvider.OPENAI] = AsyncOpenAI(
                api_key=os.getenv("OPENAI_API_KEY")
            )
        
        # Claude
        if AsyncAnthropic and os.getenv("ANTHROPIC_API_KEY"):
            self.clients[LLMProvider.CLAUDE] = AsyncAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        
        # Gemini
        if genai and os.getenv("GOOGLE_API_KEY"):
            self.clients[LLMProvider.GEMINI] = genai.Client(
                vertexai=False,
                api_key=os.getenv("GOOGLE_API_KEY")
            )

    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate completion with automatic fallback.
        
        Args:
            request: LLM request parameters
            
        Returns:
            LLMResponse with text and metadata
            
        Raises:
            Exception: If all providers fail
        """
        providers_to_try = [request.provider] if request.provider else [self.primary_provider]
        providers_to_try.extend([p for p in self.fallback_providers if p not in providers_to_try])
        
        last_error = None
        
        for provider in providers_to_try:
            if provider not in self.clients:
                logger.warning("provider_not_configured", provider=provider.value)
                continue
            
            try:
                await self.rate_limiters[provider].acquire()
                
                start_time = datetime.now()
                
                if provider == LLMProvider.OPENAI:
                    response = await self._generate_openai(request)
                elif provider == LLMProvider.CLAUDE:
                    response = await self._generate_claude(request)
                elif provider == LLMProvider.GEMINI:
                    response = await self._generate_gemini(request)
                else:
                    continue
                
                latency = (datetime.now() - start_time).total_seconds()
                response.latency_seconds = latency
                
                logger.info(
                    "llm_request_completed",
                    provider=provider.value,
                    model=response.model,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    cost_usd=response.cost_usd,
                    latency_seconds=latency,
                )
                
                return response
                
            except Exception as e:
                last_error = e
                logger.warning(
                    "llm_request_failed",
                    provider=provider.value,
                    error=str(e),
                )
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")

    async def _generate_openai(self, request: LLMRequest) -> LLMResponse:
        """Generate using OpenAI API."""
        client = self.clients[LLMProvider.OPENAI]
        model = request.model or self.DEFAULT_MODELS[LLMProvider.OPENAI]
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        text = response.choices[0].message.content
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        cost = self._calculate_cost(LLMProvider.OPENAI, model, input_tokens, output_tokens)
        
        return LLMResponse(
            text=text,
            provider=LLMProvider.OPENAI,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_seconds=0.0,  # Will be set by generate()
            timestamp=datetime.now(),
        )

    async def _generate_claude(self, request: LLMRequest) -> LLMResponse:
        """Generate using Claude API."""
        client = self.clients[LLMProvider.CLAUDE]
        model = request.model or self.DEFAULT_MODELS[LLMProvider.CLAUDE]
        
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        
        response = await client.messages.create(
            model=model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        text = response.content[0].text
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        cost = self._calculate_cost(LLMProvider.CLAUDE, model, input_tokens, output_tokens)
        
        return LLMResponse(
            text=text,
            provider=LLMProvider.CLAUDE,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_seconds=0.0,
            timestamp=datetime.now(),
        )

    async def _generate_gemini(self, request: LLMRequest) -> LLMResponse:
        """Generate using Gemini API (optimized for Indonesian)."""
        client = self.clients[LLMProvider.GEMINI]
        model = request.model or self.DEFAULT_MODELS[LLMProvider.GEMINI]
        
        # Use async client
        chat = client.aio.chats.create(model=model)
        
        full_prompt = request.prompt
        if request.system_prompt:
            full_prompt = f"System: {request.system_prompt}\n\nUser: {request.prompt}"
        
        response = await chat.send_message(full_prompt)
        
        text = response.text
        # Gemini doesn't provide token counts in the basic API
        # Estimate: ~4 characters per token
        input_tokens = len(full_prompt) // 4
        output_tokens = len(text) // 4
        
        cost = self._calculate_cost(LLMProvider.GEMINI, model, input_tokens, output_tokens)
        
        return LLMResponse(
            text=text,
            provider=LLMProvider.GEMINI,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            latency_seconds=0.0,
            timestamp=datetime.now(),
        )

    def _calculate_cost(
        self,
        provider: LLMProvider,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """Calculate cost based on provider pricing."""
        if provider not in self.COST_PER_1K:
            return 0.0
        
        model_pricing = self.COST_PER_1K[provider].get(model, {})
        input_cost = model_pricing.get("input", 0.0)
        output_cost = model_pricing.get("output", 0.0)
        
        total_cost = (input_tokens / 1000 * input_cost) + (output_tokens / 1000 * output_cost)
        return total_cost

    async def close(self):
        """Close all client connections."""
        for provider, client in self.clients.items():
            try:
                if provider == LLMProvider.OPENAI and client:
                    await client.close()
                # Claude and Gemini don't have explicit close methods in Python SDK
            except Exception as e:
                logger.warning("client_close_error", provider=provider.value, error=str(e))

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()