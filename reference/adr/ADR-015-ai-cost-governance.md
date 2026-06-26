# ADR-015: AI Cost Governance — Measurable, Traceable, Enforceable

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture's AI Platform performs millions of AI provider calls annually. Each call has a cost that depends on the provider, model, input tokens, output tokens, and prompt version. At the target scale of 100,000 stories, the AI Platform will execute approximately:

- 100,000 canonical story extractions
- 100,000 knowledge extractions
- 100,000 knowledge normalizations
- 100,000 knowledge validations
- 100,000 article generations (4 types × 25,000 each)
- 16,300,000 embedding generations (for stories, articles, entities, claims, transcript segments)

Total estimated AI provider cost at scale: **$50,000–$150,000 per year**, depending on provider selection, transcript length, and prompt optimization.

Without cost governance, the following failure modes occur:

1. **Cost explosion**: A prompt change that doubles token usage (e.g., "provide full context for every entity") silently doubles operational costs. A team member testing a new prompt on 10,000 stories incurs $500–$1,500 in unexpected costs.

2. **No cost attribution**: Costs cannot be attributed to tenants, workspaces, or content types. A tenant that generates 10× more content than others pays the same as a tenant that generates almost nothing. There is no basis for usage-based billing.

3. **No provider optimization**: Without per-provider cost data, the platform cannot determine whether Gemini, Claude, or OpenAI is more cost-effective for specific tasks. Cost optimization decisions are based on intuition, not data.

4. **Budget overruns**: Monthly AI costs exceed budget with no warning. The first indication of a cost problem is the cloud bill.

5. **No cost-per-story visibility**: The team cannot answer the question "how much does it cost to process one story?" This makes it impossible to estimate costs for new content, plan budgets, or evaluate ROI.

## Technical Context

The AI Platform PRD §17 requires: "Every execution must store: Provider, Model, Prompt Version, Input Tokens, Output Tokens, Cost, Execution Time, Tenant, Workspace, Job. Supported Analytics: Cost Per Story, Cost Per Article, Cost Per Tenant, Cost Per Workspace, Cost Per Provider."

The existing cost tracking infrastructure:

- **ADR-004 Rule 8** (Queue-Driven AI Platform): `ai_cost_log` table records provider, model, prompt version, token counts, cost in micro-dollars, execution time, provider latency, tenant_id, workspace_id per execution.
- **ADR-009 Rule 5** (AI Provider Abstraction): `CostTrackingDecorator` wraps every provider call and records cost data to `ai_cost_log`.
- **ADR-010** (Prompt Registry): Prompt version is recorded in every cost log entry, enabling cost-per-prompt analysis.

The provider cost landscape (as of June 2026):

| Provider | Model | Input Cost (per 1M tokens) | Output Cost (per 1M tokens) | Embedding Cost (per 1M tokens) |
|----------|-------|---------------------------|----------------------------|-------------------------------|
| Gemini | 2.5 Pro | $1.25 | $5.00 | — |
| Gemini | 2.5 Flash | $0.15 | $0.60 | — |
| Gemini | text-embedding-004 | — | — | $0.10 |
| Claude | 4 Opus | $15.00 | $75.00 | — |
| Claude | 4 Sonnet | $3.00 | $15.00 | — |
| OpenAI | GPT-4o | $2.50 | $10.00 | — |
| OpenAI | GPT-4o Mini | $0.15 | $0.60 | — |
| OpenAI | text-embedding-3-small | — | — | $0.02 |
| OpenAI | text-embedding-3-large | — | — | $0.13 |

## Constraints

1. **Every AI call must be tracked**: No AI provider call should execute without recording cost data. The `CostTrackingDecorator` (ADR-009) enforces this.

2. **Cost attribution per tenant and workspace**: Costs must be attributed to the tenant and workspace that triggered the AI operation. This enables usage-based billing and cost allocation.

3. **Cost per story/article**: The platform must be able to answer "how much did this story cost to process?" This requires correlating all AI operations across the pipeline for a single story.

4. **Provider comparison**: The platform must support cost comparison across providers for the same task type, enabling data-driven provider selection.

5. **Budget limits**: The platform must support per-tenant and global budget limits. When a budget is exceeded, AI processing for that tenant should be paused or restricted.

6. **Real-time cost visibility**: Cost data must be available in near real-time (minutes, not hours) for operational decision-making.

7. **Historical cost data**: Cost data must be retained for at least 1 year for trend analysis and annual planning.

8. **No performance impact**: Cost tracking must not add measurable latency to AI operations (< 5ms overhead per call).

## Problem Statement

AI provider costs can reach $50,000–$150,000 per year at target scale. Without cost governance, costs can explode silently, cannot be attributed to tenants or content types, and cannot be compared across providers. Every AI call must record provider, model, tokens, cost, tenant, workspace, and job. Costs must be attributable per story, per tenant, and per provider. Budget limits must be enforceable. How do we design an AI cost governance system that tracks every call with < 5ms overhead, enables cost attribution across tenants/workspaces/stories, supports provider comparison, enforces budget limits, and provides real-time and historical cost visibility?

# Decision

**All AI usage is measurable, traceable, and budget-enforceable. Every AI provider call records cost data to `ai_cost_log` with provider, model, prompt version, token counts, cost in micro-dollars, execution time, tenant_id, workspace_id, and pipeline_run_id. Costs are attributable per story, per tenant, per workspace, and per provider. Budget limits are enforced at the tenant and global level. Cost dashboards provide real-time and historical visibility.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AI PLATFORM (Provider Calls)                          │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  CostTrackingDecorator (wraps EVERY provider call)                │   │
│  │                                                                   │   │
│  │  Intercepts all AIProvider methods and records:                    │   │
│  │  - provider, model, prompt_version                                │   │
│  │  - input_tokens, output_tokens                                    │   │
│  │  - input_cost_micro, output_cost_micro                            │   │
│  │  - execution_time_ms, provider_latency_ms                         │   │
│  │  - tenant_id, workspace_id, pipeline_run_id                       │   │
│  │  - job_id, user_id (if applicable)                                │   │
│  └──────────────────────┬───────────────────────────────────────────┘   │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Cost Tracking Service (async writes)                             │   │
│  │  ─────────────────────────────────────                            │   │
│  │  - Buffers cost log entries in memory                             │   │
│  │  - Batch inserts to PostgreSQL (100 entries/batch)                │   │
│  │  - Separate connection pool (no impact on business DB)            │   │
│  │  - Retries failed inserts with exponential backoff                │   │
│  └──────────────────────┬───────────────────────────────────────────┘   │
│                          │                                               │
│                          ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Budget Enforcer                                                 │   │
│  │  ──────────────                                                  │   │
│  │  - Checks budget before allowing AI call                         │   │
│  │  - Tenant-level budgets (monthly)                                │   │
│  │  - Global budgets (monthly)                                      │   │
│  │  - Per-task-type budgets (optional)                              │   │
│  │  - Actions: warn, throttle, block                                │   │
│  │  - Cache: budget state cached for 60 seconds                     │   │
│  └──────────────────────┬───────────────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     POSTGRESQL (Cost Data)                                │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  ai_cost_log (per-call cost records)                               │   │
│  │  ─────────────────────────────────                                 │   │
│  │  Core table: provider, model, tokens, cost, timing, tenant        │   │
│  │  Enriched with: pipeline_run_id for story-level cost aggregation  │   │
│  │  Appx. 16M rows/year at target scale                              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  cost_budgets (budget configuration)                              │   │
│  │  ──────────────────────────────────                               │   │
│  │  Per-tenant and global budget limits                              │   │
│  │  Monthly, quarterly, and annual budgets                           │   │
│  │  Alert thresholds at 50%, 80%, 90%, 100%                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  cost_analytics (materialized for performance)                    │   │
│  │  ──────────────────────────────────────                          │   │
│  │  Materialized views for common queries:                          │   │
│  │  - cost_per_story_monthly                                         │   │
│  │  - cost_per_tenant_monthly                                        │   │
│  │  - cost_per_provider_monthly                                      │   │
│  │  - cost_per_prompt_version                                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     OBSERVABILITY (Dashboards + Alerts)                   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Grafana Dashboards                                              │   │
│  │  ──────────────────                                              │   │
│  │  - Cost Dashboard: cost over time by provider, tenant, task      │   │
│  │  - Cost per Story: average/median/P95 cost per story             │   │
│  │  - Provider Comparison: cost and latency by provider per task     │   │
│  │  - Budget Dashboard: budget vs actual per tenant                 │   │
│  │  - Token Usage: input/output token trends                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Prometheus Alerts                                               │   │
│  │  ─────────────────                                               │   │
│  │  - ai_cost_budget_70pct: Budget 70% consumed                     │   │
│  │  - ai_cost_budget_90pct: Budget 90% consumed (Warning)           │   │
│  │  - ai_cost_budget_100pct: Budget exhausted (Critical)            │   │
│  │  - ai_cost_spike: Cost > 200% of daily average                   │   │
│  │  - ai_cost_anomaly: Cost > 3σ from 7-day moving average          │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Every Provider Call Is Tracked

The `CostTrackingDecorator` (from ADR-009) wraps every AI provider call and records cost data. This is not optional — no provider call executes without cost tracking.

```python
class CostTrackingDecorator(AIProvider):
    """Wraps an AIProvider and records cost data for every call.
    
    This decorator is transparent to business logic.
    Every call to any AIProvider method is intercepted and cost is recorded.
    """
    
    def __init__(self, provider: AIProvider):
        self._provider = provider
        self._cost_tracker = AICostTracker()
    
    async def extract_canonical_story(self, transcript, metadata, prompt_version="CANONICAL_STORY_V1"):
        start_time = time.monotonic()
        
        # Call the actual provider
        result = await self._provider.extract_canonical_story(
            transcript, metadata, prompt_version
        )
        
        # Record cost asynchronously (non-blocking)
        await self._cost_tracker.record(
            provider=self._provider.provider_name,
            model=self._provider.model_name,
            prompt_version=prompt_version,
            task_type="canonical_story_extraction",
            input_tokens=result.usage.input_tokens if result.usage else 0,
            output_tokens=result.usage.output_tokens if result.usage else 0,
            input_cost_micro=result.usage.input_cost_micro if result.usage else 0,
            output_cost_micro=result.usage.output_cost_micro if result.usage else 0,
            execution_time_ms=result.usage.execution_time_ms if result.usage else 0,
            provider_latency_ms=result.usage.provider_latency_ms if result.usage else 0,
            success=result.success,
            error_message=result.error,
            tenant_id=metadata.get('tenant_id'),
            workspace_id=metadata.get('workspace_id'),
            job_id=metadata.get('job_id'),
            pipeline_run_id=metadata.get('pipeline_run_id'),
            correlation_id=metadata.get('correlation_id'),
        )
        
        return result
    
    # All other methods follow the same pattern
    # __getattr__ delegation for methods not explicitly wrapped
```

### Rule 2: Cost Log Schema

The `ai_cost_log` table stores every AI provider call.

```sql
CREATE TABLE ai_cost_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Provider identification
    provider            VARCHAR(50) NOT NULL,     -- 'gemini', 'claude', 'openai'
    model               VARCHAR(100) NOT NULL,    -- 'gemini-2.5-pro', 'claude-4-opus', 'gpt-4o'
    
    -- Task identification
    task_type           VARCHAR(50) NOT NULL,
    -- 'canonical_story_extraction', 'knowledge_extraction', 'knowledge_normalization',
    -- 'knowledge_validation', 'article_generation', 'embedding_generation'
    
    prompt_version      VARCHAR(50),              -- 'CANONICAL_STORY_V1', null for embeddings
    prompt_name         VARCHAR(100),             -- 'story_canonicalization', null for embeddings
    
    -- Token usage
    input_tokens        INTEGER NOT NULL DEFAULT 0,
    output_tokens       INTEGER NOT NULL DEFAULT 0,
    total_tokens        INTEGER GENERATED ALWAYS AS (input_tokens + output_tokens) STORED,
    
    -- Cost in micro-dollars (1/1,000,000 USD)
    -- Using micro-dollars avoids floating-point precision issues
    input_cost_micro    BIGINT NOT NULL DEFAULT 0,
    output_cost_micro   BIGINT NOT NULL DEFAULT 0,
    total_cost_micro    BIGINT GENERATED ALWAYS AS (input_cost_micro + output_cost_micro) STORED,
    
    -- Timing
    execution_time_ms   INTEGER NOT NULL DEFAULT 0,
    provider_latency_ms INTEGER NOT NULL DEFAULT 0,
    
    -- Result
    success             BOOLEAN NOT NULL DEFAULT true,
    error_message       TEXT,
    
    -- Attribution (enables cost-per-tenant, cost-per-story, cost-per-job)
    tenant_id           UUID,
    workspace_id        UUID,
    job_id              UUID,
    pipeline_run_id     UUID,         -- Links all AI operations for a single story
    user_id             UUID,         -- Who triggered this operation (if applicable)
    
    -- Traceability
    correlation_id      UUID,
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Partition key for efficient querying
    -- Partitioned by month for performance
    created_at_month    DATE GENERATED ALWAYS AS (DATE_TRUNC('month', created_at)) STORED
) PARTITION BY RANGE (created_at_month);

-- Monthly partitions (created by scheduled job)
CREATE TABLE ai_cost_log_2026_01 PARTITION OF ai_cost_log
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
CREATE TABLE ai_cost_log_2026_02 PARTITION OF ai_cost_log
    FOR VALUES FROM ('2026-02-01') TO ('2026-03-01');
-- ... created monthly by maintenance job

-- Indexes
CREATE INDEX idx_cost_log_created_at ON ai_cost_log(created_at DESC);
CREATE INDEX idx_cost_log_tenant ON ai_cost_log(tenant_id, created_at DESC);
CREATE INDEX idx_cost_log_provider ON ai_cost_log(provider, created_at DESC);
CREATE INDEX idx_cost_log_task ON ai_cost_log(task_type, created_at DESC);
CREATE INDEX idx_cost_log_pipeline ON ai_cost_log(pipeline_run_id);
CREATE INDEX idx_cost_log_job ON ai_cost_log(job_id);
```

### Rule 3: Cost per Pipeline Run

Every AI operation for a single story is linked by `pipeline_run_id`. This enables cost-per-story queries.

```sql
-- Cost per story (aggregated across all pipeline stages)
SELECT 
    pr.pipeline_run_id,
    pr.transcript_id,
    s.title AS story_title,
    COUNT(cl.id) AS total_ai_calls,
    SUM(cl.total_tokens) AS total_tokens,
    SUM(cl.total_cost_micro) / 1000000.0 AS total_cost_usd,
    SUM(cl.input_cost_micro) / 1000000.0 AS input_cost_usd,
    SUM(cl.output_cost_micro) / 1000000.0 AS output_cost_usd,
    AVG(cl.execution_time_ms) AS avg_execution_time_ms
FROM ai_pipeline_runs pr
LEFT JOIN ai_cost_log cl ON cl.pipeline_run_id = pr.pipeline_run_id
LEFT JOIN content_stories s ON s.id = pr.story_id
WHERE pr.transcript_id = :transcriptId
GROUP BY pr.pipeline_run_id, pr.transcript_id, s.title;

-- Cost per story (simplified API response)
SELECT 
    cl.pipeline_run_id,
    SUM(cl.total_cost_micro) / 1000000.0 AS total_cost_usd
FROM ai_cost_log cl
WHERE cl.pipeline_run_id = :pipelineRunId
GROUP BY cl.pipeline_run_id;
```

**Cost-per-story breakdown (estimated)**:

| Pipeline Stage | Provider | Input Tokens | Output Tokens | Estimated Cost |
|---------------|----------|-------------|--------------|----------------|
| Canonical Story Extraction | Gemini 2.5 Pro | 4,500 | 1,280 | $0.012 |
| Knowledge Extraction | Gemini 2.5 Pro | 3,000 | 800 | $0.008 |
| Knowledge Normalization | GPT-4o Mini | 2,000 | 400 | $0.0006 |
| Knowledge Validation | Claude 4 Sonnet | 2,500 | 300 | $0.012 |
| Article Generation | Gemini 2.5 Pro | 3,500 | 2,000 | $0.014 |
| Embeddings (5 types) | OpenAI text-embedding-3-small | 2,000 | 0 | $0.0001 |
| **Total per story** | | | | **~$0.047** |

### Rule 4: Cost per Tenant

Costs are attributed to tenants for allocation and billing.

```sql
-- Cost per tenant (current month)
SELECT 
    cl.tenant_id,
    t.name AS tenant_name,
    COUNT(cl.id) AS total_calls,
    SUM(cl.total_tokens) AS total_tokens,
    SUM(cl.total_cost_micro) / 1000000.0 AS total_cost_usd,
    SUM(cl.total_cost_micro) FILTER (
        WHERE cl.task_type = 'canonical_story_extraction'
    ) / 1000000.0 AS extraction_cost_usd,
    SUM(cl.total_cost_micro) FILTER (
        WHERE cl.task_type = 'embedding_generation'
    ) / 1000000.0 AS embedding_cost_usd,
    SUM(cl.total_cost_micro) FILTER (
        WHERE cl.task_type = 'article_generation'
    ) / 1000000.0 AS article_cost_usd,
    COUNT(DISTINCT cl.job_id) AS total_jobs,
    COUNT(DISTINCT cl.pipeline_run_id) AS total_stories_processed
FROM ai_cost_log cl
JOIN identity_tenants t ON t.id = cl.tenant_id
WHERE cl.created_at >= DATE_TRUNC('month', NOW())
  AND cl.created_at < DATE_TRUNC('month', NOW()) + INTERVAL '1 month'
  AND cl.tenant_id IS NOT NULL
GROUP BY cl.tenant_id, t.name
ORDER BY total_cost_usd DESC;

-- Cost per workspace
SELECT 
    cl.tenant_id,
    cl.workspace_id,
    SUM(cl.total_cost_micro) / 1000000.0 AS total_cost_usd
FROM ai_cost_log cl
WHERE cl.created_at >= DATE_TRUNC('month', NOW())
  AND cl.workspace_id IS NOT NULL
GROUP BY cl.tenant_id, cl.workspace_id
ORDER BY total_cost_usd DESC;
```

### Rule 5: Cost per Provider

Provider comparison enables data-driven provider selection for each task type.

```sql
-- Cost comparison by provider per task type
SELECT 
    cl.task_type,
    cl.provider,
    cl.model,
    COUNT(*) AS total_calls,
    AVG(cl.input_tokens) AS avg_input_tokens,
    AVG(cl.output_tokens) AS avg_output_tokens,
    AVG(cl.total_cost_micro) / 1000000.0 AS avg_cost_per_call_usd,
    SUM(cl.total_cost_micro) / 1000000.0 AS total_cost_usd,
    AVG(cl.provider_latency_ms) AS avg_latency_ms,
    -- Cost efficiency: average cost per token
    SUM(cl.total_cost_micro) / NULLIF(SUM(cl.total_tokens), 0) AS avg_cost_per_token_micro
FROM ai_cost_log cl
WHERE cl.created_at >= NOW() - INTERVAL '30 days'
  AND cl.success = true
GROUP BY cl.task_type, cl.provider, cl.model
ORDER BY cl.task_type, avg_cost_per_call_usd ASC;

-- Dashboard query: provider cost trend over time
SELECT 
    DATE_TRUNC('day', cl.created_at) AS day,
    cl.provider,
    SUM(cl.total_cost_micro) / 1000000.0 AS daily_cost_usd,
    COUNT(*) AS total_calls
FROM ai_cost_log cl
WHERE cl.created_at >= NOW() - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', cl.created_at), cl.provider
ORDER BY day ASC;
```

**Provider cost comparison (per 1,000 calls)**:

| Task | Gemini 2.5 Pro | Claude 4 Opus | GPT-4o | Recommended | Rationale |
|------|---------------|--------------|--------|-------------|-----------|
| Story Extraction | $12 | $90 | $25 | Gemini 2.5 Pro | Best cost-quality balance for structured JSON |
| Knowledge Extraction | $8 | $60 | $18 | Gemini 2.5 Pro | Same model as extraction; pipeline consistency |
| Normalization | $0.60 | — | $0.60 | GPT-4o Mini | Cheapest adequate model; task is simple |
| Validation | $6 | $15 | $10 | Gemini 2.5 Pro | Claude better quality but 2.5× cost |
| Article Generation | $14 | $105 | $30 | Gemini 2.5 Pro | Quality difference not worth 7× cost |
| Embeddings | $0.10 | — | $0.02 | OpenAI | OpenAI embeddings are cheapest and best |

### Rule 6: Budget Configuration

Budgets are configured per tenant and globally. Multiple time windows are supported.

```sql
CREATE TABLE cost_budgets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Scope
    scope_type          VARCHAR(20) NOT NULL,  -- 'global', 'tenant', 'task_type'
    scope_id            UUID,                  -- tenant_id if scope_type = 'tenant'
                                               -- NULL if scope_type = 'global'
    
    -- Budget limits (in micro-dollars)
    monthly_limit_micro     BIGINT NOT NULL,
    quarterly_limit_micro   BIGINT,             -- NULL = not tracked
    annual_limit_micro      BIGINT,             -- NULL = not tracked
    
    -- Alert thresholds (percentage of budget)
    warn_at_pct             INTEGER NOT NULL DEFAULT 70,
    critical_at_pct         INTEGER NOT NULL DEFAULT 90,
    block_at_pct            INTEGER NOT NULL DEFAULT 100,
    
    -- Current consumption (updated by refresh job)
    current_month_micro     BIGINT NOT NULL DEFAULT 0,
    current_quarter_micro   BIGINT NOT NULL DEFAULT 0,
    current_year_micro      BIGINT NOT NULL DEFAULT 0,
    last_refreshed_at       TIMESTAMPTZ,
    
    -- Action on exhaustion
    on_exhaustion           VARCHAR(20) NOT NULL DEFAULT 'block',
    -- 'warn'   : Log warning, continue processing
    -- 'throttle': Reduce processing rate by 50%
    -- 'block'  : Stop all AI processing for this scope
    
    -- Notify
    notify_emails           TEXT[],              -- Who gets budget alerts
    
    -- Status
    is_active               BOOLEAN NOT NULL DEFAULT true,
    
    -- Metadata
    description             TEXT,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(scope_type, scope_id)
);

-- Default global budget
INSERT INTO cost_budgets 
    (scope_type, scope_id, monthly_limit_micro, warn_at_pct, 
     critical_at_pct, block_at_pct, on_exhaustion, description)
VALUES 
    ('global', NULL, 5000000000, 70, 90, 100, 'block',  -- $5,000/month
     'Global AI provider budget');

-- Per-tenant budget example
INSERT INTO cost_budgets 
    (scope_type, scope_id, monthly_limit_micro, on_exhaustion, description)
VALUES 
    ('tenant', '11111111-...', 1000000000, 'throttle',  -- $1,000/month
     'Research institution tenant budget');
```

### Rule 7: Budget Enforcement

The budget enforcer checks budget consumption before allowing AI calls.

```python
class BudgetEnforcer:
    """Enforces AI cost budgets at the tenant and global level."""
    
    def __init__(self):
        self._budget_cache = {}
        self._cache_ttl = 60  # seconds
    
    async def check_budget(
        self, 
        tenant_id: Optional[str], 
        estimated_cost_micro: int
    ) -> BudgetDecision:
        """Check if an AI operation is allowed under current budgets.
        
        Returns:
            BudgetDecision with action: 'allow', 'warn', 'throttle', 'block'
        """
        decisions = []
        
        # Check global budget
        global_budget = await self._get_budget('global', None)
        if global_budget:
            decisions.append(await self._evaluate_budget(global_budget, estimated_cost_micro))
        
        # Check tenant budget
        if tenant_id:
            tenant_budget = await self._get_budget('tenant', tenant_id)
            if tenant_budget:
                decisions.append(await self._evaluate_budget(tenant_budget, estimated_cost_micro))
        
        # Most restrictive action wins
        if any(d.action == 'block' for d in decisions):
            return BudgetDecision('block', 'Budget exceeded')
        if any(d.action == 'throttle' for d in decisions):
            return BudgetDecision('throttle', 'Approaching budget limit')
        if any(d.action == 'warn' for d in decisions):
            return BudgetDecision('warn', f"Budget at {max(d.pct for d in decisions)}%")
        
        return BudgetDecision('allow', 'Budget OK')
    
    async def _evaluate_budget(
        self, budget: Budget, estimated_cost_micro: int
    ) -> BudgetDecision:
        """Evaluate a single budget against current consumption."""
        # Refresh budget consumption if cache is stale
        if budget.last_refreshed_at is None or \
           (datetime.utcnow() - budget.last_refreshed_at).seconds > self._cache_ttl:
            await self._refresh_budget(budget)
        
        projected_consumption = budget.current_month_micro + estimated_cost_micro
        pct = (projected_consumption / budget.monthly_limit_micro) * 100
        
        if pct >= budget.block_at_pct:
            return BudgetDecision('block', 
                f"Budget at {pct:.0f}%", pct=pct)
        elif pct >= budget.critical_at_pct:
            return BudgetDecision('throttle', 
                f"Budget at {pct:.0f}%", pct=pct)
        elif pct >= budget.warn_at_pct:
            return BudgetDecision('warn', 
                f"Budget at {pct:.0f}%", pct=pct)
        
        return BudgetDecision('allow', f"Budget at {pct:.0f}%", pct=pct)
    
    async def _refresh_budget(self, budget: Budget):
        """Refresh budget consumption from actual cost data."""
        row = await db.fetch_one("""
            SELECT COALESCE(SUM(total_cost_micro), 0) AS month_total
            FROM ai_cost_log
            WHERE created_at >= DATE_TRUNC('month', NOW())
              AND ($1::uuid IS NULL OR tenant_id = $1)
        """, budget.scope_id)
        
        await db.execute("""
            UPDATE cost_budgets
            SET current_month_micro = $1,
                last_refreshed_at = NOW()
            WHERE id = $2
        """, row['month_total'], budget.id)
        
        budget.current_month_micro = row['month_total']
        budget.last_refreshed_at = datetime.utcnow()
    
    async def _get_budget(self, scope_type: str, scope_id: Optional[str]) -> Optional[Budget]:
        """Get budget from cache or database."""
        cache_key = f"{scope_type}:{scope_id or 'global'}"
        
        if cache_key in self._budget_cache:
            budget = self._budget_cache[cache_key]
            # Check if cache is still valid
            if budget.last_refreshed_at and \
               (datetime.utcnow() - budget.last_refreshed_at).seconds < self._cache_ttl:
                return budget
        
        budget = await db.fetch_one("""
            SELECT * FROM cost_budgets
            WHERE scope_type = $1 
              AND (scope_id = $2 OR ($2 IS NULL AND scope_id IS NULL))
              AND is_active = true
        """, scope_type, scope_id)
        
        if budget:
            budget_obj = Budget(**budget)
            self._budget_cache[cache_key] = budget_obj
            return budget_obj
        
        return None
```

### Rule 8: Cost Tracking Performance

Cost tracking must not add measurable latency to AI operations.

```python
class AICostTracker:
    """Records AI cost data with minimal performance impact."""
    
    def __init__(self):
        self._buffer = []
        self._buffer_lock = asyncio.Lock()
        self._flush_interval = 5  # seconds
        self._batch_size = 100
        self._total_entries = 0
        
        # Start background flush task
        asyncio.create_task(self._periodic_flush())
    
    async def record(self, **kwargs):
        """Record a cost log entry (non-blocking, buffered)."""
        entry = {
            'id': uuid.uuid4(),
            'created_at': datetime.utcnow(),
            **kwargs
        }
        
        async with self._buffer_lock:
            self._buffer.append(entry)
            self._total_entries += 1
            
            if len(self._buffer) >= self._batch_size:
                # Don't await — fire and forget
                asyncio.create_task(self._flush())
    
    async def _flush(self):
        """Flush buffered entries to PostgreSQL in batch."""
        async with self._buffer_lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer = []
        
        try:
            # Batch insert using execute_values for performance
            await db.execute_values("""
                INSERT INTO ai_cost_log 
                    (id, provider, model, task_type, prompt_version, prompt_name,
                     input_tokens, output_tokens, input_cost_micro, output_cost_micro,
                     execution_time_ms, provider_latency_ms,
                     success, error_message,
                     tenant_id, workspace_id, job_id, pipeline_run_id, user_id,
                     correlation_id, created_at)
                VALUES %s
            """, [(
                e['id'], e.get('provider'), e.get('model'), e.get('task_type'),
                e.get('prompt_version'), e.get('prompt_name'),
                e.get('input_tokens', 0), e.get('output_tokens', 0),
                e.get('input_cost_micro', 0), e.get('output_cost_micro', 0),
                e.get('execution_time_ms', 0), e.get('provider_latency_ms', 0),
                e.get('success', True), e.get('error_message'),
                e.get('tenant_id'), e.get('workspace_id'),
                e.get('job_id'), e.get('pipeline_run_id'), e.get('user_id'),
                e.get('correlation_id'), e['created_at']
            ) for e in batch])
        except Exception as e:
            logger.error(f"Failed to flush {len(batch)} cost log entries: {e}")
            # Re-queue entries for retry
            async with self._buffer_lock:
                self._buffer.extend(batch)
    
    async def _periodic_flush(self):
        """Periodic flush for entries that haven't reached batch size."""
        while True:
            await asyncio.sleep(self._flush_interval)
            await self._flush()
```

### Rule 9: Cost Analytics Materialized Views

For dashboard performance, common cost queries are pre-computed in materialized views.

```sql
-- Monthly cost by tenant
CREATE MATERIALIZED VIEW cost_analytics_tenant_monthly AS
SELECT 
    DATE_TRUNC('month', created_at) AS month,
    tenant_id,
    COUNT(*) AS total_calls,
    SUM(total_tokens) AS total_tokens,
    SUM(total_cost_micro) AS total_cost_micro,
    SUM(total_cost_micro) FILTER (WHERE task_type = 'canonical_story_extraction') / 1000000.0 AS extraction_cost,
    SUM(total_cost_micro) FILTER (WHERE task_type = 'embedding_generation') / 1000000.0 AS embedding_cost,
    SUM(total_cost_micro) FILTER (WHERE task_type = 'article_generation') / 1000000.0 AS article_cost,
    COUNT(DISTINCT pipeline_run_id) AS stories_processed
FROM ai_cost_log
GROUP BY DATE_TRUNC('month', created_at), tenant_id;

-- Monthly cost by provider
CREATE MATERIALIZED VIEW cost_analytics_provider_monthly AS
SELECT 
    DATE_TRUNC('month', created_at) AS month,
    provider,
    model,
    task_type,
    COUNT(*) AS total_calls,
    SUM(total_tokens) AS total_tokens,
    AVG(total_tokens) AS avg_tokens,
    SUM(total_cost_micro) / 1000000.0 AS total_cost,
    AVG(total_cost_micro) / 1000000.0 AS avg_cost_per_call,
    AVG(provider_latency_ms) AS avg_latency_ms,
    SUM(CASE WHEN success THEN 0 ELSE 1 END) AS total_errors
FROM ai_cost_log
GROUP BY DATE_TRUNC('month', created_at), provider, model, task_type;

-- Refresh schedule
REFRESH MATERIALIZED VIEW CONCURRENTLY cost_analytics_tenant_monthly;
REFRESH MATERIALIZED VIEW CONCURRENTLY cost_analytics_provider_monthly;
```

### Rule 10: Cost Alerts and Anomaly Detection

Automated alerts notify operators of cost anomalies.

```python
class CostAnomalyDetector:
    """Detects anomalous AI cost patterns."""
    
    async def check_anomalies(self):
        """Check for cost anomalies and trigger alerts."""
        # 1. Daily cost spike detection
        daily_cost = await db.fetch_one("""
            SELECT SUM(total_cost_micro) / 1000000.0 AS today_cost
            FROM ai_cost_log
            WHERE created_at >= CURRENT_DATE
        """)
        
        avg_daily_cost = await db.fetch_one("""
            SELECT AVG(daily_total) / 1000000.0 AS avg_daily
            FROM (
                SELECT SUM(total_cost_micro) AS daily_total
                FROM ai_cost_log
                WHERE created_at >= NOW() - INTERVAL '7 days'
                  AND created_at < CURRENT_DATE
                GROUP BY DATE(created_at)
            ) daily
        """)
        
        if daily_cost and avg_daily_cost and avg_daily_cost['avg_daily'] > 0:
            ratio = daily_cost['today_cost'] / avg_daily_cost['avg_daily']
            if ratio > 2.0:
                await alerting_service.send_alert(
                    title=f"Daily AI cost spike: {ratio:.1f}x average",
                    message=f"Today's AI cost (${daily_cost['today_cost']:.2f}) is "
                            f"{ratio:.1f} times the 7-day average (${avg_daily_cost['avg_daily']:.2f}).",
                    severity='warning',
                    metric='ai_cost_spike'
                )
        
        # 2. Monthly budget breach detection
        budgets = await db.fetch_all(
            "SELECT * FROM cost_budgets WHERE is_active = true"
        )
        
        for budget in budgets:
            pct = (budget['current_month_micro'] / budget['monthly_limit_micro']) * 100
            
            if pct >= budget['block_at_pct']:
                scope_name = budget['scope_type'] + (f" {budget['scope_id']}" if budget['scope_id'] else "")
                await alerting_service.send_alert(
                    title=f"AI Budget Exhausted: {scope_name}",
                    message=f"Budget for {scope_name} is at {pct:.0f}%. Processing is blocked.",
                    severity='critical',
                    metric='ai_cost_budget_100pct'
                )
            elif pct >= budget['critical_at_pct']:
                await alerting_service.send_alert(
                    title=f"AI Budget Critical: {pct:.0f}%",
                    message=f"Budget at {pct:.0f}%. Processing will be blocked at {budget['block_at_pct']}%.",
                    severity='warning',
                    metric='ai_cost_budget_90pct'
                )
```

**Alerting rules (Prometheus)**:

```yaml
# Prometheus alerting rules for AI cost governance
groups:
  - name: ai_cost_alerts
    rules:
      - alert: AICostBudgetExhausted
        expr: ai_cost_budget_usage_pct > 100
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "AI budget exhausted for {{ $labels.scope }}"
          
      - alert: AICostBudgetCritical
        expr: ai_cost_budget_usage_pct > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "AI budget critical at {{ $value }}% for {{ $labels.scope }}"
          
      - alert: AICostDailySpike
        expr: ai_cost_daily_total / avg(ai_cost_daily_total[7d]) > 2
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Daily AI cost spike: {{ $value }}x average"
          
      - alert: AICostAnomaly
        expr: ai_cost_hourly_total > 3 * stddev(ai_cost_hourly_total[7d])
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Anomalous AI cost detected"
```

**Grafana dashboard panels**:

| Panel | Query | Description |
|-------|-------|-------------|
| Cost Today | `SUM(ai_cost_log_total_cost_micro{created_at=~"today"})` | Current day's total AI cost |
| Cost This Month | `SUM(ai_cost_log_total_cost_micro{created_at=~"this_month"})` | Month-to-date total |
| Budget vs Actual | Gauge showing budget consumption % | Visual budget indicator |
| Cost by Provider (stacked) | `SUM(ai_cost_log_total_cost_micro) by (provider)` | Daily cost breakdown by provider |
| Cost per Story (7d) | `avg(ai_cost_log_total_cost_micro{pipeline_run_id!=""}) by (pipeline_run_id)` | Distribution of cost per story |
| Token Usage Trend | `rate(ai_cost_log_total_tokens[1h])` | Token consumption over time |
| Provider Latency P95 | `histogram_quantile(0.95, ai_cost_log_provider_latency_ms)` | Latency comparison |
| Budget Table | Table showing all budgets with % consumed | Summary of all budgets |

# Alternatives Considered

## Alternative 1: No Cost Tracking (Trust-Based)

**Description**: Do not track AI costs. Trust that teams will use AI providers responsibly. Costs are reviewed monthly on the cloud bill.

**Advantages**:
- Zero implementation cost — no tracking infrastructure to build
- No performance overhead — no cost logging code
- No database storage for cost data
- No operational burden for cost monitoring

**Disadvantages**:
- **No cost attribution**: Cannot determine which tenant, workspace, or content type is driving costs.
- **No cost optimization**: Cannot identify expensive providers, models, or prompts. Cost reduction decisions are guesses.
- **No budget enforcement**: Cannot prevent cost overruns. The first sign of a problem is the monthly bill.
- **No cost-per-story visibility**: Cannot answer "how much does it cost to process a story?" for budgeting or pricing.
- **No provider comparison**: Cannot determine which provider is most cost-effective for each task type.
- **No accountability**: Without cost attribution, there is no incentive for teams to optimize prompt efficiency.

**Rejection rationale**: Trust-based cost management is not viable at $50,000–$150,000 annual spend. The PRD explicitly requires cost tracking (§17). Without cost governance, the platform cannot make informed provider selection decisions, cannot attribute costs to tenants, and cannot prevent budget overruns.

## Alternative 2: Provider-Side Cost Reports Only

**Description**: Rely on provider-side cost reporting (Google Cloud Console, Anthropic Console, OpenAI Usage Dashboard). Do not implement application-level cost tracking. Review provider dashboards weekly or monthly.

**Advantages**:
- No implementation cost — provider dashboards are free
- Accurate billing data — provider-reported costs are the source of truth for billing
- No database storage for cost data
- No application-level performance overhead

**Disadvantages**:
- **No per-tenant cost attribution**: Provider dashboards show aggregated costs, not costs per tenant. The platform's multi-tenant architecture requires tenant-level cost attribution.
- **No per-story cost attribution**: Provider dashboards cannot correlate costs to specific pipeline runs or stories.
- **No real-time cost visibility**: Provider dashboards have hours to days of latency. Costs cannot be monitored in real-time.
- **No budget enforcement at application level**: Cannot block AI calls when budget is exceeded. Provider-side budgets are account-level, not per-tenant.
- **No cross-provider unified view**: Each provider has a different dashboard. Comparing costs across Gemini, Claude, and OpenAI requires manual spreadsheet work.
- **No cost-per-prompt-version analysis**: Provider dashboards do not track prompt versions. Cannot determine which prompt changes increased or decreased costs.
- **No integration with observability stack**: Provider dashboards cannot be integrated with Grafana, Prometheus, or the platform's alerting infrastructure.

**Rejection rationale**: Provider-side cost reports are useful for billing verification but insufficient for the platform's cost governance requirements. Application-level cost tracking is necessary for per-tenant attribution, per-story analysis, real-time visibility, unified cross-provider comparison, and budget enforcement.

## Alternative 3: Cost Tracking in Application Logs Only

**Description**: Log AI cost data as structured log entries (JSON to stdout). Use log aggregation tools (Loki, Elasticsearch) to query and analyze cost data. No dedicated cost database table.

**Advantages**:
- No database schema to design and maintain
- Cost data is already in the logging pipeline — no new infrastructure
- Log aggregation tools provide query capabilities
- Cost data is retained with existing log retention policies

**Disadvantages**:
- **Poor query performance**: Log queries are significantly slower than database queries for aggregation. A "cost per tenant this month" query that takes 50ms in PostgreSQL takes 5–30 seconds in Loki.
- **No indexing for common cost queries**: Logs are indexed by timestamp, not by tenant_id, provider, or task_type. Queries filtering by these fields are slow.
- **No budget enforcement**: Logging systems are not designed for real-time budget checks. Cannot block AI calls based on log data.
- **No cost rollup**: Logs are individual events. Monthly cost summaries require scanning all logs for the month.
- **Higher storage cost**: Structured JSON logs with cost data consume more storage than optimized database columns.
- **No partition management**: Log systems do not support monthly partitioning for cost data. Historical cost queries scan all partitions.
- **Schema evolution complexity**: Changing the cost log format requires updating log parsing pipelines. Database schema changes are simpler.

**Rejection rationale**: Log-based cost tracking is feasible for small volumes but does not scale to 16M+ entries per year with the query performance requirements for dashboards and budget enforcement. A dedicated `ai_cost_log` table with proper indexing, partitioning, and materialized views provides 100–1000x better query performance.

## Alternative 4: Real-Time Cost Streaming to External System

**Description**: Stream cost events in real-time to an external cost management system (e.g., AWS Cost Explorer, Vantage, CloudZero, or a custom cost analytics service). Do not store cost data in the platform's database.

**Advantages**:
- Cost data is managed by a dedicated system designed for cost analytics
- External systems often provide better visualization and alerting
- Reduces storage burden on the platform's database
- External systems may provide AI-specific cost optimization recommendations
- Cost data is separated from operational data (security boundary)

**Disadvantages**:
- **Additional infrastructure**: Requires deploying and managing an external cost management system or service.
- **Network latency**: Streaming cost events adds latency and a potential failure point.
- **External dependency**: If the cost management system is unavailable, cost data is lost or queued.
- **No local cost data**: Cost queries that join with platform data (e.g., "cost per story that was reviewed by this editor") require cross-system joins.
- **Higher cost**: External cost management services charge additional fees based on data volume.
- **Data residency**: Cost data may need to stay in the same region as the platform. External services may not support the required region.
- **Integration complexity**: Building and maintaining the streaming pipeline adds ongoing engineering effort.

**Rejection rationale**: An external cost management system is a valuable complement but not a replacement for local cost tracking. The platform needs cost data locally for joins with operational data (pipeline runs, reviews, tenant activity) and for budget enforcement that cannot tolerate network latency. The local `ai_cost_log` table provides low-latency, always-available cost data. External cost management can be added as an additional export destination for long-term trend analysis and optimization recommendations.

# Consequences

## Positive

1. **Complete cost visibility**: Every AI provider call is recorded with provider, model, tokens, cost, tenant, and task type. Cost data is available in real-time with < 5 seconds of latency.

2. **Cost attribution per tenant**: Costs are attributed to the tenant and workspace that triggered the AI operation. This enables usage-based billing, cost allocation, and fair resource sharing across tenants.

3. **Cost per story**: All AI operations for a single story are linked by `pipeline_run_id`. The total cost to process a story is queryable. Average cost per story: ~$0.047 at target scale.

4. **Provider comparison**: Cost and latency data per provider per task type enables data-driven provider selection. Dashboards show which provider is most cost-effective for each pipeline stage.

5. **Budget enforcement**: Tenant-level and global budgets are enforced at the application level. Processing is blocked, throttled, or warned based on configurable thresholds.

6. **Cost anomaly detection**: Automated alerts detect cost spikes (> 2× daily average) and anomalies (> 3σ from 7-day moving average). Operators are notified before cost issues become critical.

7. **Prompt version cost analysis**: Prompt version is recorded in every cost log entry. The cost impact of prompt changes is measurable. A prompt change that doubles token usage is immediately visible.

8. **No performance impact**: Cost tracking is asynchronous and buffered. The critical path for AI operations is not affected. Batch inserts (100 entries) and background flushes (5-second interval) ensure < 1ms overhead per call.

## Negative

1. **Storage growth**: The `ai_cost_log` table grows by ~16M rows per year at target scale. With monthly partitioning and archiving, active storage is manageable but requires maintenance.

2. **Implementation complexity**: Cost tracking, budget enforcement, materialized views, and anomaly detection require significant implementation effort (estimated 2–4 weeks).

3. **Cost calculation accuracy**: Provider pricing changes over time. The cost calculation logic in adapters and the cost tracker must be kept in sync with provider pricing updates.

4. **No automatic provider switching**: The system can recommend cheaper providers but does not automatically switch. Manual intervention is required to update the provider factory configuration.

5. **Budget enforcement latency**: Budget consumption is cached with 60-second TTL. An aggressive tenant could exceed their budget by a small amount before the budget check catches up.

6. **Cost attribution edge cases**: Some AI operations may not have a clear tenant_id (e.g., system-level normalization, background reindexing). These costs are attributed to the system, not to any tenant.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Cost visibility** | Every call tracked with provider/model/tokens | 16M rows/year storage growth |
| **Cost attribution** | Per-tenant, per-story, per-job attribution | Some edge cases with no clear tenant |
| **Budget enforcement** | Block/throttle at configurable thresholds | 60-second cache latency for budget state |
| **Provider comparison** | Data-driven provider selection | Requires manual config updates |
| **Performance** | < 1ms overhead per call (async buffered) | Implementation complexity (2–4 weeks) |
| **Alerting** | Automated anomaly detection | Alert tuning required to avoid noise |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Cost log batch insert fails** | Low | Medium — cost entries lost | Buffer re-queues failed entries. Retry with exponential backoff. Alert on persistent failures. |
| **Budget cache returns stale data** | Medium | Low — tenant exceeds budget by small amount | 60-second TTL limits exposure. Hard block at 105% as safety net. |
| **Provider pricing changes break cost calculations** | Medium | Medium — reported costs are inaccurate | Centralized pricing configuration. Alert on cost calculation mismatch. Monthly pricing audit. |
| **Cost log table partition management fails** | Low | Medium — new partitions not created | Automated partition creation (scheduled job). Alert when next month's partition does not exist. |
| **Correlation ID missing for some operations** | Medium | Medium — cannot link costs to pipeline runs | Make correlation_id optional in the schema. Log warning when missing. Backfill from job_id where possible. |
| **High-volume embedding generation overwhelms cost tracker** | Low | Medium — buffer grows, flush delayed | Monitor buffer size. Auto-scale flush frequency. Separate embedding cost tracker from LLM cost tracker. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Budget incorrectly configured** | Medium | High — processing blocked incorrectly | Test budget configuration in staging. Require admin approval for budget changes. Default budget is generous (no block). |
| **Cost anomaly alerts too noisy** | Medium | Low — alert fatigue | Tune anomaly detection thresholds. Suppress alerts during known high-activity periods. Weekly alert review. |
| **Materialized views stale** | Medium | Low — dashboard shows yesterday's data | Refresh materialized views every hour. Dashboard shows "Last refreshed: X minutes ago". |
| **Developer forgets to add cost tracking for new task type** | Medium | Medium — new AI operations not tracked | CostTrackingDecorator wraps ALL AIProvider methods. CI test verifies all AIProvider methods are wrapped. |
| **Provider cost calculation logic not updated after price change** | Medium | Medium — reported cost differs from actual bill | Quarterly pricing audit. Compare platform-reported costs with provider invoices. Alert on > 5% discrepancy. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **AI provider costs decrease significantly** | Cost governance becomes less critical | Reduce alert frequency. Keep infrastructure for optimization decisions. |
| **Self-hosted LLMs eliminate per-call costs** | Cost tracking model no longer applies | Adapt cost tracker for infrastructure costs (GPU hours). Track utilization instead of per-call cost. |
| **Usage-based tenant billing required** | Must bill tenants based on AI usage | Cost attribution by tenant already implemented. Add billing integration layer. |
| **Regulatory requirement for AI cost transparency** | Must report AI costs per content type | Cost data by task_type already available. Extend reporting for regulatory compliance. |
| **Fine-tuned models have different cost structure** | Fixed training cost + variable inference cost | Extend cost model to amortize training costs across inference calls. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Self-hosted LLMs deployed**: If the platform deploys self-hosted models (e.g., Llama 3, fine-tuned domain model), the cost model changes from per-token to per-GPU-hour. The cost tracker must be adapted to track infrastructure costs alongside or instead of per-call costs.

2. **Usage-based tenant billing implemented**: If the platform bills tenants based on AI usage, the cost attribution model must be extended with billing rates, invoice generation, and payment tracking. The existing `tenant_id` attribution provides the foundation.

3. **Fine-tuned models with amortized training costs**: If the platform fine-tunes models on Indonesian folklore data, the training cost must be amortized across inference calls. The cost tracker should support blended cost rates that include training amortization.

4. **Real-time cost optimization with automatic provider switching**: If the platform implements automatic provider switching based on real-time cost and quality data, the provider factory (ADR-009) should be extended to accept cost-based routing decisions from the cost governance system.

5. **Carbon footprint tracking**: If the platform needs to track the carbon footprint of AI operations (relevant for sustainability reporting), extend the cost log to include estimated energy consumption and carbon emissions per provider call.

# References

- **AI Platform PRD §17** — "Cost Governance" — Every execution must store provider, model, prompt version, tokens, cost, execution time, tenant, workspace, job.
- **AI Platform PRD §14** — "Provider Strategy" — Primary/fallback provider configuration for cost optimization.
- **ADR-004 Rule 8** — "Cost Tracking on Every Execution" — `ai_cost_log` table definition with micro-dollars.
- **ADR-009 Rule 5** — "Cost Tracking Decorator" — Wraps every provider call with cost recording.
- **ADR-009 Rule 4** — "Task-Specific Provider Selection" — Per-task provider configuration for cost optimization.
- **ADR-010** — "Prompt Registry Governance" — Prompt version recorded in cost data for cost-per-prompt analysis.
- **OpenAI Pricing** — https://openai.com/pricing — Token-based pricing for GPT-4o, GPT-4o Mini, and embedding models.
- **Google AI Pricing** — https://ai.google.dev/pricing — Token-based pricing for Gemini models.
- **Anthropic Pricing** — https://www.anthropic.com/pricing — Token-based pricing for Claude models.
- **Micro-dollars (µ$)** — 1 micro-dollar = $0.000001. Using integers for cost storage avoids floating-point precision issues. $1.00 = 1,000,000 micro-dollars.