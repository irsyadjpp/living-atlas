# ADR-009: AI Provider Abstraction — No Direct Provider Calls in Business Logic

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture's AI Platform performs five core operations using Large Language Models:

1. **Canonical Story Extraction** — Transform transcript into structured canonical story JSON
2. **Knowledge Extraction** — Extract entities, claims, beliefs, rituals from canonical story
3. **Knowledge Normalization** — Resolve aliases, consolidate entities, detect duplicates
4. **Knowledge Validation** — Confidence scoring, schema validation, contradiction detection
5. **Article Generation** — Generate narrative, knowledge, news, and creative articles

These operations are the intellectual core of the platform. If any single AI provider becomes unavailable, expensive, or produces poor results, the entire pipeline stalls. The platform must be resilient to provider failures, cost changes, and quality degradation without requiring code changes to business logic.

The AI Platform PRD §3.5 states: "Business logic must never depend on a specific provider." The provider strategy (§14) is Gemini primary, Claude fallback, OpenAI secondary fallback.

## Technical Context

The AI Platform consists of Python 3.14 workers that call external AI providers via their respective SDKs:

- **Gemini** — `google-generativeai` SDK (Google AI)
- **Claude** — `anthropic` SDK (Anthropic)
- **OpenAI** — `openai` SDK (OpenAI)

Each provider has different:
- API formats (request/response structures)
- Rate limits and pricing models
- Model capabilities (context window size, output format reliability, JSON mode support)
- Latency profiles (p50/p95/p99 response times)
- Availability SLAs
- Content filtering policies (which may block culturally sensitive Indonesian folklore content)

Provider costs vary significantly:
- Gemini 2.5 Pro: ~$0.50–$1.50 per story extraction (depending on transcript length)
- Claude 4 Opus: ~$2.00–$5.00 per story extraction
- OpenAI GPT-4o: ~$1.50–$3.00 per story extraction

At 100,000 stories × average 3 provider calls per story = 300,000 calls, a $1 per call difference equals $300,000 in annual cost. Provider selection is not just a technical decision — it is a cost decision.

## Constraints

1. **No provider hardcoding**: Business logic (extraction, knowledge extraction, article generation) must never import or call a provider SDK directly. All provider access goes through the abstraction layer.

2. **Automatic failover**: If the primary provider (Gemini) is unavailable, rate-limited, or returns errors, the system must automatically failover to Claude, then to OpenAI. Failover must be transparent to business logic.

3. **Provider-agnostic prompts**: Prompts must be written in a provider-agnostic way. They must not use provider-specific features (e.g., Gemini's function calling, Claude's XML tags, OpenAI's JSON mode) in a way that makes them non-portable.

4. **Cost tracking per provider**: Every AI call must record the provider used, model used, token counts, and cost. Cost analytics must support provider comparison and optimization.

5. **Testing without real providers**: Unit tests must work without calling real AI providers. The abstraction layer must support a mock/stub provider for testing.

6. **Provider-specific optimizations**: While business logic must be provider-agnostic, the adapter layer may use provider-specific features (e.g., Gemini's `response_mime_type="application/json"` for reliable JSON output) to improve quality. These optimizations are encapsulated in the adapter.

7. **Graceful degradation**: When all providers are unavailable, the system must not lose data. Jobs must remain in the queue for retry, not fail silently.

8. **Future provider support**: The abstraction must support adding new providers (e.g., local models, fine-tuned domain models) without modifying existing business logic.

## Problem Statement

AI workers need to call LLM providers for canonical story extraction, knowledge extraction, normalization, validation, and article generation. The platform must support Gemini, Claude, and OpenAI (with future providers). Business logic must never depend on a specific provider's SDK, API format, or feature set. The system must automatically failover between providers, track costs per provider, and support testing with mock providers. How do we design a provider abstraction layer that encapsulates provider-specific details behind a common interface, enables transparent failover, supports cost optimization, and allows new providers to be added without modifying business logic?

# Decision

**Business logic never directly calls Gemini, Claude, or OpenAI. All providers are accessed through a common abstraction layer consisting of: (1) a Provider Interface defining AI operations, (2) provider-specific Adapters implementing the interface, (3) a Provider Factory with failover logic, (4) a Cost Tracking decorator wrapping every call. Business logic calls the factory, gets a provider, and calls the interface. It never knows which provider is actually serving the request.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      AI WORKER (Business Logic)                           │
│                                                                          │
│  Business logic calls AIProvider interface only.                         │
│  Never imports provider SDKs. Never knows which provider is serving.     │
│                                                                          │
│  extraction_service.py:                                                  │
│    provider = AIProviderFactory.get_provider(task="canonical_story")     │
│    result = await provider.extract_canonical_story(transcript, meta)     │
│                                                                          │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROVIDER ABSTRACTION LAYER                             │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  AIProvider Interface (ABC)                       │   │
│  │                                                                   │   │
│  │  + extract_canonical_story(transcript, metadata) → ExtractionResult│   │
│  │  + extract_knowledge(canonical_story) → KnowledgeResult           │   │
│  │  + normalize_knowledge(knowledge) → NormalizationResult           │   │
│  │  + validate_knowledge(knowledge) → ValidationResult               │   │
│  │  + generate_article(canonical_story, type) → ArticleResult        │   │
│  │  + generate_embeddings(text, model) → EmbeddingResult             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│            ┌─────────────┼──────────────┐                              │
│            ▼             ▼              ▼                               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                    │
│  │    Gemini    │ │    Claude    │ │    OpenAI    │                    │
│  │   Adapter   │ │   Adapter    │ │   Adapter    │                    │
│  │             │ │              │ │              │                    │
│  │ Google AI   │ │  Anthropic   │ │  OpenAI      │                    │
│  │ SDK         │ │  SDK         │ │  SDK         │                    │
│  └──────┬──────┘ └──────┬───────┘ └──────┬───────┘                    │
│         │               │                │                             │
│         ▼               ▼                ▼                             │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  AIProviderFactory                                 │   │
│  │                                                                   │   │
│  │  get_provider(task, preferred=None) → AIProvider                   │   │
│  │                                                                   │   │
│  │  1. Try preferred or primary (Gemini)                             │   │
│  │  2. If failover condition → try next (Claude)                     │   │
│  │  3. If failover condition → try next (OpenAI)                     │   │
│  │  4. If all fail → raise AllProvidersUnavailableError              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                          │                                              │
│                          ▼                                              │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │              CostTrackingDecorator (wraps every call)              │   │
│  │                                                                   │   │
│  │  - Records provider, model, prompt_version                        │   │
│  │  - Records input_tokens, output_tokens                            │   │
│  │  - Records execution_time_ms, provider_latency_ms                 │   │
│  │  - Calculates cost from token counts + provider pricing           │   │
│  │  - Writes to ai_cost_log table                                    │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                  MockProvider (for testing)                        │   │
│  │                                                                   │   │
│  │  - Returns canned responses from fixture files                    │   │
│  │  - Simulates provider failures for testing failover               │   │
│  │  - Validates that prompts produce valid JSON Schema output        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Provider Interface Defines All AI Operations

The `AIProvider` abstract base class defines every AI operation. Business logic calls the interface only. No business logic file imports `google-generativeai`, `anthropic`, or `openai`.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

# ── Data Classes ──────────────────────────────────────────────────────────

@dataclass
class ProviderUsage:
    """Token usage and cost for a single provider call."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost_micro: int       # Cost in micro-dollars (1/1,000,000 USD)
    output_cost_micro: int
    total_cost_micro: int
    provider: str               # 'gemini', 'claude', 'openai'
    model: str                  # 'gemini-2.5-pro', 'claude-4-opus', 'gpt-4o'
    prompt_version: str         # 'CANONICAL_STORY_V1'
    execution_time_ms: int
    provider_latency_ms: int    # Time waiting for provider response

@dataclass
class ProviderResult:
    """Base result for all provider operations."""
    success: bool
    data: dict                  # Parsed response data
    usage: ProviderUsage
    raw_response: str           # Original response text (for debugging)
    error: Optional[str] = None

# ── Abstract Interface ────────────────────────────────────────────────────

class AIProvider(ABC):
    """Abstract interface for all AI provider operations.
    
    Business logic calls these methods only. It never knows which
    provider (Gemini, Claude, OpenAI) is actually serving the request.
    """
    
    @abstractmethod
    async def extract_canonical_story(
        self, 
        transcript: str, 
        metadata: dict, 
        prompt_version: str = "CANONICAL_STORY_V1"
    ) -> ProviderResult:
        """Extract a canonical story from a transcript."""
        pass
    
    @abstractmethod
    async def extract_knowledge(
        self, 
        canonical_story: dict, 
        prompt_version: str = "KNOWLEDGE_EXTRACTION_V1"
    ) -> ProviderResult:
        """Extract knowledge objects, entities, claims from a canonical story."""
        pass
    
    @abstractmethod
    async def normalize_knowledge(
        self,
        knowledge: dict,
        existing_entities: list[dict],
        prompt_version: str = "KNOWLEDGE_NORMALIZATION_V1"
    ) -> ProviderResult:
        """Normalize knowledge: resolve aliases, consolidate entities, detect duplicates."""
        pass
    
    @abstractmethod
    async def validate_knowledge(
        self,
        canonical_story: dict,
        knowledge: dict,
        prompt_version: str = "KNOWLEDGE_VALIDATION_V1"
    ) -> ProviderResult:
        """Validate extracted knowledge: confidence scoring, schema validation, contradiction detection."""
        pass
    
    @abstractmethod
    async def generate_article(
        self,
        canonical_story: dict,
        knowledge: dict,
        article_type: str,        # 'narrative', 'knowledge', 'news', 'creative'
        prompt_version: str = "NARRATIVE_ARTICLE_V1"
    ) -> ProviderResult:
        """Generate a publication-ready article from validated knowledge."""
        pass
    
    @abstractmethod
    async def generate_embeddings(
        self,
        text: str,
        model: str = "text-embedding-3-small"
    ) -> ProviderResult:
        """Generate vector embeddings for text content."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name (e.g., 'gemini', 'claude', 'openai')."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name (e.g., 'gemini-2.5-pro', 'claude-4-opus')."""
        pass
```

### Rule 2: Provider Adapters Encapsulate SDK Details

Each provider has an adapter class that implements the `AIProvider` interface. Provider-specific logic (authentication, request formatting, response parsing, error handling, retry logic) is encapsulated in the adapter.

```python
# ── Gemini Adapter ────────────────────────────────────────────────────────

class GeminiProvider(AIProvider):
    """Adapter for Google Gemini API."""
    
    def __init__(self, config: ProviderConfig):
        import google.generativeai as genai
        genai.configure(api_key=config.api_key)
        self.model = genai.GenerativeModel(
            config.model_name or "gemini-2.5-pro",
            generation_config={
                "temperature": config.temperature or 0.2,
                "top_p": 0.95,
                "response_mime_type": "application/json",  # Gemini-specific: forces JSON output
            }
        )
        self._provider_name = "gemini"
        self._model_name = config.model_name or "gemini-2.5-pro"
    
    async def extract_canonical_story(self, transcript, metadata, prompt_version="CANONICAL_STORY_V1"):
        prompt = PromptRegistry.get(prompt_version)
        filled_prompt = prompt.format(transcript=transcript, metadata=json.dumps(metadata))
        
        start_time = time.monotonic()
        try:
            response = await self.model.generate_content_async(filled_prompt)
            provider_latency = int((time.monotonic() - start_time) * 1000)
            
            # Parse JSON response (Gemini returns JSON text when response_mime_type is set)
            data = json.loads(response.text)
            
            usage = ProviderUsage(
                input_tokens=response.usage_metadata.prompt_token_count,
                output_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count,
                input_cost_micro=calculate_gemini_cost(
                    "input", response.usage_metadata.prompt_token_count),
                output_cost_micro=calculate_gemini_cost(
                    "output", response.usage_metadata.candidates_token_count),
                total_cost_micro=0,  # Calculated in decorator
                provider=self._provider_name,
                model=self._model_name,
                prompt_version=prompt_version,
                execution_time_ms=provider_latency,
                provider_latency_ms=provider_latency
            )
            
            return ProviderResult(
                success=True, data=data, usage=usage, raw_response=response.text
            )
            
        except Exception as e:
            return ProviderResult(
                success=False, data={}, usage=None, raw_response="",
                error=f"Gemini API error: {str(e)}"
            )
    
    @property
    def provider_name(self): return self._provider_name
    
    @property
    def model_name(self): return self._model_name


# ── Claude Adapter ────────────────────────────────────────────────────────

class ClaudeProvider(AIProvider):
    """Adapter for Anthropic Claude API."""
    
    def __init__(self, config: ProviderConfig):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
        self._model_name = config.model_name or "claude-4-opus"
        self._provider_name = "claude"
    
    async def extract_canonical_story(self, transcript, metadata, prompt_version="CANONICAL_STORY_V1"):
        prompt = PromptRegistry.get(prompt_version)
        filled_prompt = prompt.format(transcript=transcript, metadata=json.dumps(metadata))
        
        start_time = time.monotonic()
        try:
            # Claude uses a system prompt + user message structure
            response = await self.client.messages.create(
                model=self._model_name,
                max_tokens=4096,
                system="You are a cultural knowledge extraction assistant. "
                       "Always respond with valid JSON matching the requested schema. "
                       "Never hallucinate entities or claims not present in the transcript.",
                messages=[{"role": "user", "content": filled_prompt}]
            )
            provider_latency = int((time.monotonic() - start_time) * 1000)
            
            # Claude returns JSON as text content block
            data = json.loads(response.content[0].text)
            
            usage = ProviderUsage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                input_cost_micro=calculate_claude_cost(
                    "input", response.usage.input_tokens),
                output_cost_micro=calculate_claude_cost(
                    "output", response.usage.output_tokens),
                total_cost_micro=0,
                provider=self._provider_name,
                model=self._model_name,
                prompt_version=prompt_version,
                execution_time_ms=provider_latency,
                provider_latency_ms=provider_latency
            )
            
            return ProviderResult(
                success=True, data=data, usage=usage, 
                raw_response=response.content[0].text
            )
            
        except Exception as e:
            return ProviderResult(
                success=False, data={}, usage=None, raw_response="",
                error=f"Claude API error: {str(e)}"
            )
    
    @property
    def provider_name(self): return self._provider_name
    
    @property
    def model_name(self): return self._model_name
```

### Rule 3: Provider Factory with Transparent Failover

The factory encapsulates provider selection and failover logic. Business logic calls `AIProviderFactory.get_provider(task)` and receives a provider without knowing which one.

```python
class AIProviderFactory:
    """Creates AI provider instances with automatic failover.
    
    Business logic calls get_provider() and receives a configured provider.
    If the preferred provider is unavailable, the factory automatically
    fails over to the next provider in the chain.
    """
    
    # Provider configuration per task
    # Each task can have a different provider strategy
    TASK_PROVIDER_CONFIG = {
        "canonical_story": {
            "primary": {"provider": "gemini", "model": "gemini-2.5-pro"},
            "fallbacks": [
                {"provider": "claude", "model": "claude-4-opus"},
                {"provider": "openai", "model": "gpt-4o"},
            ],
            "prompt_version": "CANONICAL_STORY_V1",
        },
        "knowledge_extraction": {
            "primary": {"provider": "gemini", "model": "gemini-2.5-pro"},
            "fallbacks": [
                {"provider": "openai", "model": "gpt-4o"},
                {"provider": "claude", "model": "claude-4-sonnet"},
            ],
            "prompt_version": "KNOWLEDGE_EXTRACTION_V1",
        },
        "normalization": {
            "primary": {"provider": "openai", "model": "gpt-4o-mini"},
            # Normalization is cheaper — use gpt-4o-mini as primary
            "fallbacks": [
                {"provider": "gemini", "model": "gemini-2.5-flash"},
            ],
            "prompt_version": "KNOWLEDGE_NORMALIZATION_V1",
        },
        "validation": {
            "primary": {"provider": "claude", "model": "claude-4-sonnet"},
            # Validation benefits from Claude's instruction-following
            "fallbacks": [
                {"provider": "gemini", "model": "gemini-2.5-pro"},
                {"provider": "openai", "model": "gpt-4o"},
            ],
            "prompt_version": "KNOWLEDGE_VALIDATION_V1",
        },
        "article_generation": {
            "primary": {"provider": "gemini", "model": "gemini-2.5-pro"},
            "fallbacks": [
                {"provider": "claude", "model": "claude-4-opus"},
                {"provider": "openai", "model": "gpt-4o"},
            ],
            "prompt_version": "NARRATIVE_ARTICLE_V1",  # Overridden per article type
        },
        "embeddings": {
            "primary": {"provider": "openai", "model": "text-embedding-3-small"},
            # OpenAI embeddings are industry standard and cost-effective
            "fallbacks": [
                {"provider": "gemini", "model": "text-embedding-004"},
            ],
            "prompt_version": None,  # Embeddings don't use prompts
        },
    }
    
    _instances: dict = {}
    _config: ProviderConfig = None
    
    @classmethod
    def initialize(cls, config: ProviderConfig):
        """Initialize the factory with provider credentials and configuration."""
        cls._config = config
        cls._instances = {}
    
    @classmethod
    async def get_provider(
        cls, 
        task: str, 
        preferred: Optional[str] = None
    ) -> AIProvider:
        """Get a provider for the given task with automatic failover.
        
        Args:
            task: The AI task type (e.g., 'canonical_story', 'knowledge_extraction')
            preferred: Optional override to try a specific provider first
            
        Returns:
            A configured AIProvider instance
            
        Raises:
            AllProvidersUnavailableError: If no provider is available
        """
        if task not in cls.TASK_PROVIDER_CONFIG:
            raise UnknownTaskError(f"Unknown task: {task}")
        
        task_config = cls.TASK_PROVIDER_CONFIG[task]
        
        # Build provider chain: preferred → primary → fallbacks
        provider_chain = []
        if preferred:
            provider_chain.append(preferred)
        provider_chain.append(task_config["primary"]["provider"])
        for fallback in task_config["fallbacks"]:
            if fallback["provider"] not in provider_chain:
                provider_chain.append(fallback["provider"])
        
        # Try each provider in the chain
        last_error = None
        for provider_name in provider_chain:
            try:
                # Check if provider is available (rate limit, health)
                if not await cls._is_provider_available(provider_name):
                    logger.warning(f"Provider {provider_name} is not available, trying next")
                    continue
                
                # Get or create provider instance
                provider = cls._get_or_create_provider(provider_name, task_config)
                
                # Health check: try a simple completion
                if await provider.health_check():
                    logger.info(f"Using provider {provider_name} for task {task}")
                    return provider
                
            except AllProvidersUnavailableError:
                raise
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider_name} failed: {e}")
                continue
        
        # All providers failed
        error_msg = f"All providers unavailable for task {task}. Last error: {last_error}"
        logger.critical(error_msg)
        raise AllProvidersUnavailableError(error_msg)
    
    @classmethod
    def _get_or_create_provider(cls, provider_name: str, task_config: dict) -> AIProvider:
        """Create or return a cached provider instance."""
        cache_key = f"{provider_name}"
        if cache_key in cls._instances:
            return cls._instances[cache_key]
        
        # Find the model config for this provider
        provider_config = task_config["primary"]
        model_name = provider_config["model"]
        for fallback in task_config["fallbacks"]:
            if fallback["provider"] == provider_name:
                model_name = fallback["model"]
                break
        
        # Create provider instance
        config = cls._config.get_provider_config(provider_name, model_name)
        
        if provider_name == "gemini":
            provider = GeminiProvider(config)
        elif provider_name == "claude":
            provider = ClaudeProvider(config)
        elif provider_name == "openai":
            provider = OpenAIProvider(config)
        else:
            raise UnknownProviderError(f"Unknown provider: {provider_name}")
        
        # Wrap with cost tracking decorator
        provider = CostTrackingDecorator(provider)
        
        cls._instances[cache_key] = provider
        return provider
    
    @classmethod
    async def _is_provider_available(cls, provider_name: str) -> bool:
        """Check if a provider is available based on rate limits and health."""
        if provider_name not in cls._config.providers:
            return False
        
        provider_config = cls._config.providers[provider_name]
        
        # Check rate limit state
        rate_limiter = RateLimiterRegistry.get(provider_name)
        if rate_limiter and rate_limiter.is_throttled():
            logger.info(f"Provider {provider_name} is rate-limited, skipping")
            return False
        
        # Check if provider is manually disabled
        if provider_config.get("disabled", False):
            return False
        
        return True
```

**Failover conditions**:

| Condition | Action | Recovery |
|-----------|--------|----------|
| HTTP 429 (Rate Limited) | Skip to next provider | Retry primary after rate limit window expires |
| HTTP 5xx (Server Error) | Skip to next provider | Retry primary on next job attempt |
| Timeout (>30s) | Skip to next provider | Retry primary on next job attempt |
| Invalid API key | Skip provider permanently | Alert operator to check credentials |
| Content filtered by provider | Skip to next provider (may have different filters) | Log blocked content for review |
| JSON parse error in response | Skip to next provider | Log malformed response for debugging |
| All providers fail | Raise AllProvidersUnavailableError | Job remains in queue for later retry |

### Rule 4: Task-Specific Provider Selection

Different AI tasks have different requirements. The factory allows per-task provider configuration.

```python
# Different tasks use different provider strategies:
#
# canonical_story:       Gemini 2.5 Pro (primary) → Claude 4 Opus → GPT-4o
#                        Gemini's JSON mode is most reliable for structured output
#
# knowledge_extraction:  Gemini 2.5 Pro (primary) → GPT-4o → Claude 4 Sonnet
#                        Similar to extraction; Gemini preferred for cost
#
# normalization:         GPT-4o Mini (primary) → Gemini 2.5 Flash
#                        Cheaper models sufficient for entity matching
#
# validation:            Claude 4 Sonnet (primary) → Gemini 2.5 Pro → GPT-4o
#                        Claude has best instruction-following for validation
#
# article_generation:    Gemini 2.5 Pro (primary) → Claude 4 Opus → GPT-4o
#                        Creative writing quality is priority
#
# embeddings:            OpenAI text-embedding-3-small (primary) → Gemini embedding-004
#                        OpenAI embeddings are industry standard
```

**Rationale for per-task selection**:
- **Cost optimization**: Expensive models (Claude Opus, GPT-4o) are reserved for tasks where quality matters most (extraction, article generation). Cheaper models (GPT-4o Mini, Gemini Flash) are used for simpler tasks (normalization).
- **Provider strengths**: Claude is preferred for validation (best instruction-following). Gemini is preferred for structured JSON extraction (`response_mime_type="application/json"`). OpenAI is preferred for embeddings (industry-standard quality and cost).
- **Failover diversity**: Fallback providers are chosen to be qualitatively different from the primary. If Gemini has a systemic issue (e.g., content filtering), Claude may not have the same issue.

### Rule 5: Cost Tracking Decorator

Every provider call is wrapped in a decorator that records cost data. Cost tracking is transparent to both business logic and provider adapters.

```python
class CostTrackingDecorator(AIProvider):
    """Wraps an AIProvider and records cost data for every call.
    
    This decorator is transparent to callers. Business logic
    receives a decorated provider and calls it normally.
    The decorator intercepts the result and writes cost data
    to the ai_cost_log table.
    """
    
    def __init__(self, provider: AIProvider):
        self._provider = provider
    
    async def extract_canonical_story(self, transcript, metadata, prompt_version="CANONICAL_STORY_V1"):
        result = await self._provider.extract_canonical_story(
            transcript, metadata, prompt_version
        )
        await self._record_cost(result, prompt_version)
        return result
    
    async def _record_cost(self, result: ProviderResult, prompt_version: str):
        """Record cost data to PostgreSQL."""
        if not result.usage:
            return
        
        usage = result.usage
        
        # Calculate total cost
        usage.total_cost_micro = usage.input_cost_micro + usage.output_cost_micro
        
        await db.execute("""
            INSERT INTO ai_cost_log
                (provider, model, prompt_version,
                 input_tokens, output_tokens, total_tokens,
                 input_cost_micro, output_cost_micro, total_cost_micro,
                 execution_time_ms, provider_latency_ms,
                 created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
        """, usage.provider, usage.model, usage.prompt_version,
             usage.input_tokens, usage.output_tokens, usage.total_tokens,
             usage.input_cost_micro, usage.output_cost_micro, usage.total_cost_micro,
             usage.execution_time_ms, usage.provider_latency_ms)
    
    # Delegate all other methods to the wrapped provider
    def __getattr__(self, name):
        return getattr(self._provider, name)
```

### Rule 6: Mock Provider for Testing

A `MockProvider` implementation enables testing without calling real AI providers.

```python
class MockProvider(AIProvider):
    """Mock provider that returns canned responses from fixture files.
    
    Used for:
    - Unit tests (no provider credentials needed)
    - Integration tests (deterministic responses)
    - CI/CD pipeline (no external dependencies)
    - Load testing (no rate limit concerns)
    """
    
    def __init__(self, fixture_dir: str = "tests/fixtures/providers"):
        self.fixture_dir = fixture_dir
        self._call_history = []
        self._failure_mode = None  # None, "rate_limit", "timeout", "server_error"
    
    async def extract_canonical_story(self, transcript, metadata, prompt_version="CANONICAL_STORY_V1"):
        self._call_history.append({
            "method": "extract_canonical_story",
            "prompt_version": prompt_version,
            "transcript_length": len(transcript)
        })
        
        if self._failure_mode:
            return self._simulate_failure()
        
        return self._load_fixture("canonical_story_response.json")
    
    def set_failure_mode(self, mode: Optional[str]):
        """Set failure mode for testing failover logic."""
        self._failure_mode = mode
    
    def get_call_history(self) -> list:
        """Return call history for verifying provider selection."""
        return self._call_history.copy()
    
    def _simulate_failure(self) -> ProviderResult:
        if self._failure_mode == "rate_limit":
            return ProviderResult(False, {}, None, "", 
                error="429 Too Many Requests")
        elif self._failure_mode == "timeout":
            return ProviderResult(False, {}, None, "",
                error="Request timed out after 30s")
        elif self._failure_mode == "server_error":
            return ProviderResult(False, {}, None, "",
                error="500 Internal Server Error")
        return ProviderResult(False, {}, None, "", error="Unknown error")
    
    def _load_fixture(self, fixture_name: str) -> ProviderResult:
        import json
        with open(f"{self.fixture_dir}/{fixture_name}") as f:
            data = json.load(f)
        
        usage = ProviderUsage(
            input_tokens=500, output_tokens=200, total_tokens=700,
            input_cost_micro=50, output_cost_micro=100, total_cost_micro=150,
            provider="mock", model="mock-model", prompt_version="test",
            execution_time_ms=100, provider_latency_ms=100
        )
        
        return ProviderResult(True, data, usage, json.dumps(data))
    
    @property
    def provider_name(self): return "mock"
    
    @property
    def model_name(self): return "mock-model"
```

**Test example**:
```python
async def test_failover_when_primary_rate_limited():
    """Test that factory falls back to secondary when primary is rate limited."""
    
    # Configure factory with mock providers
    config = ProviderConfig(testing=True)
    AIProviderFactory.initialize(config)
    
    # Make the factory return mock providers
    mock_gemini = MockProvider()
    mock_gemini.set_failure_mode("rate_limit")
    mock_claude = MockProvider()
    
    AIProviderFactory._instances = {
        "gemini": mock_gemini,
        "claude": mock_claude,
    }
    
    # Get provider — should skip rate-limited Gemini and return Claude
    provider = await AIProviderFactory.get_provider("canonical_story")
    
    assert provider.provider_name == "claude", \
        f"Expected claude but got {provider.provider_name}"
    
    # Verify Gemini was tried first
    assert len(mock_gemini.get_call_history()) >= 1

async def test_all_providers_unavailable():
    """Test that AllProvidersUnavailableError is raised when all providers fail."""
    
    config = ProviderConfig(testing=True)
    AIProviderFactory.initialize(config)
    
    # Make all providers fail
    for name in ["gemini", "claude", "openai"]:
        mock = MockProvider()
        mock.set_failure_mode("server_error")
        AIProviderFactory._instances[name] = mock
    
    with pytest.raises(AllProvidersUnavailableError):
        await AIProviderFactory.get_provider("canonical_story")
```

### Rule 7: Provider-Agnostic Prompt Design

Prompts must be written in a way that does not depend on provider-specific features. Provider-specific optimizations (Gemini's `response_mime_type`, Claude's XML prompting, OpenAI's JSON mode) are applied in the adapter layer, not in the prompt.

```python
# ── Provider-Agnostic Prompt ─────────────────────────────────────────────

PROMPT_CANONICAL_STORY_V1 = """
You are a cultural knowledge extraction assistant for The Living Atlas of Indonesian Mystery Culture.

Your task is to extract a structured canonical story from the following transcript.

TRANSCRIPT:
{transcript}

METADATA:
{metadata}

INSTRUCTIONS:
1. Extract the core narrative: title, summary, narrative type, cultural context.
2. Identify all named entities: spirits, creatures, people, locations.
3. Extract claims with supporting evidence from the transcript.
4. Identify themes, motifs, beliefs, and rituals mentioned.
5. Note any contradictions or uncertainties.
6. NEVER invent entities or claims not present in the transcript.
7. Preserve cultural specificity — use original language names.
8. For every extracted item, reference the transcript segment that supports it.

OUTPUT FORMAT:
Respond with a JSON object matching the Canonical Story Schema v1.
{
  "story": { "title": "...", "summary": "...", ... },
  "entities": [...],
  "claims": [...],
  "themes": [...],
  "motifs": [...],
  "beliefs": [...],
  "rituals": [...],
  "contradictions": [...],
  "uncertainties": [...]
}
"""

# ── Provider-Specific Optimizations (in Adapter) ─────────────────────────
# These are NOT in the prompt. They are applied by the adapter.

# Gemini adapter:
#   Sets response_mime_type="application/json" so Gemini returns JSON directly
#   This is Gemini-specific — other providers ignore this setting

# Claude adapter:
#   Uses system prompt + user message structure
#   Claude's system prompt is a separate API parameter
#   The prompt text itself is provider-agnostic

# OpenAI adapter:
#   Uses response_format={"type": "json_object"} for reliable JSON
#   This is OpenAI-specific — other providers ignore this setting
```

### Rule 8: Provider Health Checks

The factory periodically checks provider health to make informed failover decisions.

```python
class ProviderHealthChecker:
    """Periodically checks provider health for informed failover decisions."""
    
    def __init__(self):
        self._health_status: dict[str, HealthStatus] = {}
        self._check_interval = 60  # seconds
    
    async def check_provider(self, provider_name: str, provider: AIProvider) -> HealthStatus:
        """Check provider health with a minimal test call."""
        try:
            start = time.monotonic()
            # Use a minimal, cheap test completion
            result = await provider.health_check()
            latency = int((time.monotonic() - start) * 1000)
            
            status = HealthStatus(
                available=True,
                latency_ms=latency,
                last_checked=datetime.utcnow(),
                error=None
            )
        except Exception as e:
            status = HealthStatus(
                available=False,
                latency_ms=None,
                last_checked=datetime.utcnow(),
                error=str(e)
            )
        
        self._health_status[provider_name] = status
        return status
    
    def is_available(self, provider_name: str) -> bool:
        """Check if provider is currently considered available."""
        status = self._health_status.get(provider_name)
        if not status:
            return True  # Unknown = assume available
        if not status.available:
            # Allow retry after backoff period
            if datetime.utcnow() - status.last_checked > timedelta(minutes=5):
                return True  # Stale failure — retry
            return False
        return True
```

### Rule 9: Embedding Provider Abstraction

Embeddings have different requirements than LLM calls. They are abstracted through the same interface but with provider-specific considerations.

```python
class OpenAIEmbeddingProvider(AIProvider):
    """Adapter for OpenAI Embeddings API."""
    
    def __init__(self, config: ProviderConfig):
        import openai
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
        self._model_name = config.model_name or "text-embedding-3-small"
        self._provider_name = "openai"
    
    async def generate_embeddings(self, text: str, model: str = None) -> ProviderResult:
        model = model or self._model_name
        start_time = time.monotonic()
        
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=text,
                encoding_format="float"  # Returns list of floats
            )
            provider_latency = int((time.monotonic() - start_time) * 1000)
            
            usage = ProviderUsage(
                input_tokens=response.usage.prompt_tokens,
                output_tokens=0,  # Embeddings don't have output tokens
                total_tokens=response.usage.prompt_tokens,
                input_cost_micro=calculate_openai_embedding_cost(
                    response.usage.prompt_tokens, model),
                output_cost_micro=0,
                total_cost_micro=0,
                provider=self._provider_name,
                model=model,
                prompt_version="embeddings",
                execution_time_ms=provider_latency,
                provider_latency_ms=provider_latency
            )
            
            return ProviderResult(
                success=True,
                data={"embedding": response.data[0].embedding, "model": model},
                usage=usage,
                raw_response=str(response)
            )
        except Exception as e:
            return ProviderResult(
                success=False, data={}, usage=None, raw_response="",
                error=f"OpenAI Embedding error: {str(e)}"
            )
```

# Alternatives Considered

## Alternative 1: Direct Provider SDK Calls in Business Logic

**Description**: Business logic imports and calls provider SDKs directly. Each AI worker (extraction, knowledge, article) calls `google.generativeai`, `anthropic`, or `openai` directly. No abstraction layer.

**Advantages**:
- Simplest possible implementation — no abstraction overhead
- Full access to provider-specific features in business logic
- No adapter code to write and maintain
- Easier debugging — stack traces show direct SDK calls
- Faster initial development

**Disadvantages**:
- **Hardcoded provider coupling**: Changing from Gemini to Claude requires rewriting every AI worker. At 6 workers × 5 operations = 30 code paths to update.
- **No transparent failover**: Each worker must implement its own failover logic. Most developers will skip failover, leading to brittle code.
- **No centralized cost tracking**: Each worker must implement its own cost logging. Most will forget, leading to incomplete cost data.
- **Testing requires real credentials**: Unit tests cannot run without valid API keys. CI/CD pipeline requires provider access.
- **Vendor lock-in**: Provider-specific features (Gemini's `response_mime_type`, Claude's XML prompting) become embedded in business logic. Switching providers requires rewriting prompts and response parsers.
- **Inconsistent error handling**: Worker A handles rate limits with retry. Worker B does not. Worker C has a bug in retry logic. The platform becomes inconsistent.
- **No cost optimization**: The system cannot automatically route tasks to the cheapest suitable provider because there is no centralized provider selection logic.

**Rejection rationale**: Direct SDK calls in business logic violate the PRD requirement (§3.5), create vendor lock-in, eliminate transparent failover, and make testing dependent on real provider credentials. The abstraction layer adds minimal overhead (a function call + adapter indirection) while providing significant benefits in flexibility, resilience, and testability.

## Alternative 2: Generic HTTP Client with Provider URLs

**Description**: Instead of provider-specific SDKs and adapters, use a generic HTTP client that calls provider APIs directly via their REST endpoints. Provider-specific details (URLs, authentication headers, request formats) are stored in configuration files. The abstraction layer is a single generic client that maps AI operations to REST calls.

**Advantages**:
- Single client implementation instead of N adapters
- Provider configuration is purely data (URLs, headers, prompt templates)
- Adding a new provider requires only configuration changes, not code
- No SDK dependency management (no `google-generativeai`, `anthropic`, `openai` pip packages)

**Disadvantages**:
- **Each provider's REST API is fundamentally different**: Gemini uses `generateContent`, Claude uses `messages.create`, OpenAI uses `chat.completions`. The request/response structures, authentication methods, streaming options, and error formats are all different. The generic client must handle N different API formats, making it more complex than N adapters.
- **No SDK optimizations**: Provider SDKs handle retries, rate limiting, connection pooling, and request batching. Reimplementing these for a generic HTTP client is error-prone and duplicates SDK maintainer effort.
- **API changes require client updates**: When a provider changes their REST API (e.g., adding a new required field), the generic client must be updated. SDKs are maintained by the provider and updated proactively.
- **JSON mode, streaming, and function calling**: Each provider implements these features differently. A generic HTTP client must handle N different JSON mode implementations, N different streaming formats, etc.
- **Authentication complexity**: Gemini uses API keys in headers. Claude uses `x-api-key` headers. OpenAI uses `Authorization: Bearer` headers. The generic client must handle these differences.
- **Testing complexity**: The generic HTTP client must mock N different API responses. Provider SDKs provide built-in testing utilities.

**Rejection rationale**: A generic HTTP client replaces N provider-specific adapters with 1 hyper-complex client that must understand N different API formats. This is not simpler — it just moves complexity from adapters to the client. Provider SDKs provide valuable abstractions (retry, rate limiting, connection management) that would need to be reimplemented. The adapter pattern is cleaner because each adapter is simple (maps one SDK to the interface) and new providers can be added without modifying existing adapters.

## Alternative 3: Provider Abstraction in Backend (Java) Instead of AI Platform (Python)

**Description**: Move the provider abstraction layer to the Java backend. The backend calls AI providers directly (via REST or SDK) and returns results to the AI Platform workers. The AI Platform becomes a thin orchestration layer that delegates all AI calls to the backend.

**Advantages**:
- Java Spring Boot has mature HTTP client infrastructure (WebClient, RestTemplate, retry, circuit breakers)
- Backend can reuse existing monitoring, logging, and cost tracking infrastructure
- Centralized provider management in one service
- AI Platform workers become simpler (no provider SDKs, no API keys)

**Disadvantages**:
- **Direct violation of AI Platform PRD §3.1**: "Forbidden: Backend → AI Platform REST." If the backend calls AI providers, it must do so via REST, which violates the queue-driven architecture.
- **Synchronous AI calls in backend**: Backend API performance would degrade (p95 < 300ms target) if it makes synchronous AI provider calls that take 10–120 seconds.
- **Backend thread pool exhaustion**: 100 concurrent AI extraction calls would exhaust the backend thread pool, blocking user-facing API requests.
- **Added network hop**: Backend → AI Provider instead of AI Worker → AI Provider. This adds latency and a potential failure point.
- **Language mismatch**: Java's AI/ML ecosystem (LangChain4j, Spring AI) is less mature than Python's. Provider SDKs are Python-first (Gemini, Claude, OpenAI all provide Python SDKs; Java SDKs may lag).
- **Backend complexity**: The backend would need to manage provider-specific logic (rate limiting, failover, cost tracking) that is more naturally handled in the AI Platform.

**Rejection rationale**: Moving provider calls to the backend violates the queue-driven AI architecture, degrades backend API performance, and adds unnecessary network hops. The AI Platform (Python) is the correct place for AI provider abstraction because it aligns with the architecture (queue-driven, async, separate scaling) and the language ecosystem (Python has the best AI provider SDKs). The abstraction layer is implemented in Python within the AI Platform workers.

## Alternative 4: Single Provider Only (Gemini)

**Description**: Use Gemini as the sole AI provider. No abstraction layer, no failover, no multi-provider support. All AI operations use Gemini exclusively.

**Advantages**:
- Simplest possible architecture — no abstraction, no adapters, no failover logic
- Single SDK to learn, maintain, and debug
- Consistent output format (Gemini's JSON mode)
- No multi-provider testing complexity
- Lower initial infrastructure cost (one API key, one provider relationship)

**Disadvantages**:
- **Single point of failure**: If Google AI is down, the entire AI pipeline stops. No failover. At 99.5% availability target, even short Google AI outages are unacceptable.
- **Vendor lock-in**: All prompts, response parsers, and business logic are Gemini-specific. Switching providers requires a complete rewrite.
- **No cost optimization**: Cannot route tasks to cheaper providers. If Gemini raises prices, the platform has no alternatives.
- **No redundancy for content filtering**: If Gemini's content filters block culturally sensitive folklore content (a real concern for Indonesian mystery culture), there is no alternative provider with different filtering policies.
- **No competitive pressure**: Without the ability to switch providers, the platform has no leverage for pricing negotiation or quality improvements.
- **Single model limitations**: Different tasks benefit from different models (Claude for validation, GPT-4o Mini for normalization, Gemini for structured output). A single provider limits model diversity.

**Rejection rationale**: Single-provider dependency creates unacceptable business risk. At 99.5% availability target, the platform cannot depend on a single external provider. The abstraction layer exists specifically to eliminate this dependency. The cost of building and maintaining the abstraction layer (estimated 2–4 weeks initial development, ongoing maintenance) is far less than the cost of a provider outage or forced migration.

# Consequences

## Positive

1. **No vendor lock-in**: Business logic never imports provider SDKs. Changing providers requires only a new adapter class — no changes to extraction, knowledge, or article generation logic.

2. **Transparent failover**: The factory automatically fails over between providers. If Gemini is rate-limited, Claude serves the request. If Claude is down, OpenAI serves. Business logic never sees the failover.

3. **Per-task provider optimization**: Different tasks use different providers. Canonical story extraction uses Gemini (best JSON output). Validation uses Claude (best instruction-following). Normalization uses GPT-4o Mini (cheapest adequate model). This optimizes both quality and cost.

4. **Complete cost tracking**: Every provider call is wrapped by the `CostTrackingDecorator`, which records provider, model, tokens, cost, and latency to `ai_cost_log`. Cost analytics are available per provider, per task, per tenant, and per prompt version.

5. **Testability**: The `MockProvider` enables testing without real provider credentials. Unit tests run in CI/CD without external dependencies. Failover logic can be tested deterministically by setting failure modes.

6. **Easy provider addition**: Adding a new provider (e.g., a local LLM, a fine-tuned domain model) requires one new adapter class and one configuration entry. No business logic changes. No existing adapter changes.

7. **Provider-agnostic prompts**: Prompts are written to be provider-independent. Provider-specific features (JSON mode, system prompts) are applied in the adapter layer. Prompts can be reused across providers.

8. **Graceful degradation**: When all providers are unavailable, `AllProvidersUnavailableError` is raised. Jobs remain in the Redpanda queue and are retried. No data loss. No silent failures.

## Negative

1. **Abstraction overhead**: Every AI call goes through 3 layers (business logic → interface → adapter → SDK). This adds ~5–15ms of overhead per call. For calls that take 10–120 seconds of provider latency, this overhead is negligible (0.01–0.15%).

2. **Adapter maintenance**: Each provider adapter must be maintained as provider SDKs and APIs evolve. When Google releases a new Gemini SDK version, the `GeminiProvider` adapter must be updated. This is estimated at 1–2 days of work per provider per quarter.

3. **Provider-specific features unavailable in business logic**: If a provider introduces a powerful new feature (e.g., Claude's "extended thinking"), business logic cannot use it until the adapter exposes it through the interface. This may delay adoption of new capabilities.

4. **Testing complexity for failover logic**: Testing all failover scenarios (rate limit → fallback, timeout → fallback, all providers unavailable) requires careful setup of mock providers with specific failure modes. Failover tests are more complex than single-provider tests.

5. **Configuration overhead**: Per-task provider configuration must be maintained and tuned. As provider pricing and capabilities change, the configuration must be updated to reflect the optimal provider for each task.

6. **Cost calculation complexity**: Each provider has different pricing models (per-token for Gemini, per-character for Claude, per-token with different rates for input/output for OpenAI). The cost calculation logic in each adapter must be kept in sync with provider pricing changes.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Vendor lock-in** | Eliminated — business logic has no provider dependency | Adapter maintenance as provider SDKs evolve |
| **Resilience** | Transparent failover between providers | Complex failover testing |
| **Cost optimization** | Per-task provider selection | Configuration overhead for provider mapping |
| **Testing** | Mock provider enables CI/CD testing | Must maintain realistic fixtures |
| **Feature access** | Provider-agnostic prompts | New provider features delayed by adapter updates |
| **Observability** | Centralized cost tracking | Cost calculation logic must track pricing changes |
| **Simplicity** | Multi-provider resilience | 3+ adapters instead of 1 direct SDK integration |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Provider SDK upgrade breaks adapter** | Medium | Medium — adapter fails | Pin SDK versions. Run integration tests in CI. Monitor provider changelogs. Maintain fallback providers during migration. |
| **Provider API changes pricing model** | Medium | High — cost calculations incorrect | Centralized pricing configuration. Alert on cost anomalies. Periodic pricing audit. |
| **Provider deprecates model** | Low | High — model unavailable | Factory falls back to next provider. Update adapter configuration to use new model. Monitor provider deprecation notices. |
| **Content filtering differs per provider** | Medium | Medium — some content blocked by one provider but not another | Failover provides implicit mitigation. Log blocked content for review. If all providers block, flag for human review. |
| **Rate limit synchronization across provider instances** | Medium | Low — multiple workers hit same rate limit | Centralized rate limit tracking in Redis. Coordinate across worker instances. |
| **Mock provider fixtures become stale** | Medium | Medium — tests pass but real provider behavior differs | Periodically regenerate fixtures from real provider responses. Run smoke tests against real providers in staging. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **All providers unavailable simultaneously** | Low | Critical — pipeline stalls | Jobs remain in Redpanda queue. Alert on-call. Implement manual override to route to backup provider or suspend automated processing. |
| **Cost tracking logs overwhelm database** | Low | Medium — increased storage cost | Batch insert cost logs (100 records per batch). Archive logs after 90 days. Implement sampling for high-volume tasks. |
| **Developer bypasses abstraction layer** | Medium | High — provider coupling introduced | Code review enforces no provider SDK imports in business logic. CI scan detects prohibited imports. ArchUnit-style tests in Python (`flake8` plugin). |
| **Per-task provider configuration becomes outdated** | Medium | Medium — suboptimal provider selection | Quarterly review of provider pricing and capabilities. Automated cost analytics dashboard. Alert when alternative provider would be cheaper for a task. |
| **Provider credentials exposed in logs** | Low | Critical — security incident | Sanitize API keys in log output. Use secret manager (not config files) for credentials. Mask keys in error messages. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Local LLM deployment requires different abstraction** | Adapter interface may not fit local model characteristics | Extend interface with streaming, batching, and model-specific parameters. Local model adapter inherits from AIProvider with additional methods. |
| **Fine-tuned domain models replace general LLMs** | Provider abstraction may not capture model-specific capabilities | Add `capabilities` property to provider interface. Business logic can query capabilities and choose appropriate provider. |
| **Multi-modal input (audio, video, images)** | Interface designed for text input only | Extend interface with multi-modal support. Add `media` parameter to relevant methods. Each adapter handles media format differently. |
| **AI provider market consolidation** | Fewer providers to choose from reduces failover options | Maintain at least 2 active providers. Consider open-source models as additional fallback. Document migration path to self-hosted models. |
| **Regulatory requirements for AI explainability** | Must record which provider and model processed each request | Already covered by cost tracking (provider, model, prompt version). Extend with reasoning/explanation data from provider if available. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Local LLM deployment**: If the platform deploys self-hosted models (e.g., Llama 3, Mistral, or a fine-tuned domain model), the provider abstraction must be extended with a local model adapter. Local models have different characteristics (no API keys, no rate limits, different latency profiles) that may require interface extensions.

2. **Fine-tuned domain models**: If the platform fine-tunes models on Indonesian folklore data, these models may be specialized for extraction tasks. The provider factory should prioritize fine-tuned models over general-purpose providers for relevant tasks.

3. **Multi-modal AI operations**: If the platform processes audio (directly, not via transcript) or images (folklore illustrations, location photos), the provider interface must be extended with multi-modal methods. Each adapter handles media input differently.

4. **Streaming responses**: If the platform needs real-time AI features (streaming article generation, interactive research assistance), the provider interface should support streaming. This is a significant interface change that affects all adapters.

5. **Agent-based AI workflows**: If the platform needs multi-step AI reasoning (research agents, fact-checking agents), the current single-call interface pattern must be extended to support conversation history, tool use, and multi-turn interactions.

6. **Provider market changes**: If a major provider exits the market or significantly changes pricing/capabilities, the per-task provider configuration must be updated. The abstraction layer itself remains valid.

# References

- **AI Platform PRD §3.5** — "Model Agnostic Architecture" — Business logic must never depend on a specific provider.
- **AI Platform PRD §13** — "AI Provider Layer" — Provider Interface → Gemini/Claude/OpenAI Adapters.
- **AI Platform PRD §14** — "Provider Strategy" — Gemini primary, Claude fallback, OpenAI secondary fallback.
- **AI Platform PRD §17** — "Cost Governance" — Per-execution cost tracking.
- **ADR-004: Queue-Driven AI Platform** — AI workers are the consumers of the provider abstraction.
- **ADR-007: Canonical Story Core Contract** — Provider output must conform to Canonical Story schema.
- **Abstract Factory Pattern** — https://refactoring.guru/design-patterns/abstract-factory — Encapsulating provider-specific logic behind a common interface.
- **Decorator Pattern** — https://refactoring.guru/design-patterns/decorator — Wrapping provider calls with cost tracking.
- **Google Generative AI SDK** — https://github.com/google-gemini/generative-ai-python — Python SDK for Gemini API.
- **Anthropic Python SDK** — https://github.com/anthropics/anthropic-sdk-python — Python SDK for Claude API.
- **OpenAI Python SDK** — https://github.com/openai/openai-python — Python SDK for OpenAI API.
- **Circuit Breaker Pattern** — https://martinfowler.com/bliki/CircuitBreaker.html — Pattern for handling provider failures (future consideration).