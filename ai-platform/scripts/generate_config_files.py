#!/usr/bin/env python3
"""Generate .env configuration template for enrichment and article services."""

from pathlib import Path


def generate_env_template():
    """Generate .env template with all required configuration."""
    
    env_content = """# ============================================================
# Living Atlas AI Platform — Environment Configuration
# ============================================================
# Enrichment & Article Services Implementation
# PRD v2.0 Compliance
# ============================================================

# --- PostgreSQL ---
LA_PG_HOST=localhost
LA_PG_PORT=5432
LA_PG_DATABASE=living_atlas
LA_PG_USER=living_atlas
LA_PG_PASSWORD=living_atlas
LA_PG_MIN_CONNECTIONS=2
LA_PG_MAX_CONNECTIONS=10

# --- Redpanda / Kafka ---
LA_KAFKA_BOOTSTRAP_SERVERS=localhost:9092
LA_KAFKA_CONSUMER_GROUP=ai-platform

# --- Redis ---
LA_REDIS_URL=redis://localhost:6379/0

# --- Third-party LLM API Keys ---
# PRIMARY: Gemini 1.5 Flash (for enrichment - cost-effective, 1M context)
GEMINI_API_KEY=your_gemini_api_key_here

# SECONDARY: Claude 3.5 Sonnet (for article generation - best writing quality)
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# FALLBACK: OpenAI GPT-4o (for embeddings and fallback)
OPENAI_API_KEY=your_openai_api_key_here

# --- STT API Keys (Fallback for extraction service) ---
GOOGLE_APPLICATION_CREDENTIALS=./infrastructure/secrets/gcp-credentials.json
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here

# --- Weaviate (for embeddings - Phase 2+) ---
LA_WEAVIATE_URL=http://localhost:8080
LA_WEAVIATE_API_KEY=

# --- Prefect (for orchestration - Phase 2+) ---
LA_PREFECT_API_URL=http://localhost:4200/api

# --- Service Configuration ---
LA_SERVICE_NAME=enrichment-service
LA_SERVICE_PORT=8002

# --- Logging ---
LA_LOG_LEVEL=INFO

# --- Observability ---
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317

# --- Model Selection ---
# LLM provider for enrichment (gemini | claude | openai)
LLM_PROVIDER=gemini

# LLM provider for article generation (claude | gemini | openai)
ARTICLE_LLM_PROVIDER=claude

# --- Rate Limiting Configuration ---
# Max concurrent LLM requests
MAX_CONCURRENT_LLM_REQUESTS=10

# Max concurrent STT requests
MAX_CONCURRENT_STT_REQUESTS=5

# --- Cost Thresholds ---
# Daily cost limit in USD
DAILY_COST_LIMIT=20.0

# Alert threshold (percentage of daily limit)
COST_ALERT_THRESHOLD=0.5

# --- Retry Configuration ---
# Maximum retry attempts for external APIs
MAX_RETRY_ATTEMPTS=5

# Initial retry delay in seconds
RETRY_INITIAL_DELAY=30

# Maximum retry delay in seconds
RETRY_MAX_DELAY=300

# --- Processing Configuration ---
# Maximum transcript length for enrichment (characters)
MAX_TRANSCRIPT_LENGTH=15000

# Maximum knowledge objects length (characters)
MAX_KNOWLEDGE_OBJECTS_LENGTH=5000

# Chunk size for long transcripts (tokens)
TRANSCRIPT_CHUNK_SIZE=150000

# Chunk overlap in tokens
TRANSCRIPT_CHUNK_OVERLAP=5000

# --- Quality Thresholds ---
# Minimum confidence score for claims
MIN_CLAIM_CONFIDENCE=0.6

# Minimum quality score for articles
MIN_ARTICLE_QUALITY_SCORE=0.5

# Hallucination detection threshold
HALLUCINATION_THRESHOLD=0.8
"""
    
    return env_content


def generate_api_setup_guide():
    """Generate guide for setting up external APIs."""
    
    guide_content = """# External API Setup Guide

This guide explains how to obtain and configure the required API keys for the AI Platform enrichment and article services.

## Required APIs

### 1. Google Gemini API (Primary for Enrichment)

**Purpose:** Primary LLM for knowledge extraction (cost-effective, 1M token context)

**Steps:**
1. Go to https://aistudio.google.com/app/apikey
2. Create a new project or select existing project
3. Generate API key for Gemini API
4. Copy the API key to `.env` as `GEMINI_API_KEY`

**Configuration:**
- Primary model: gemini-1.5-flash ($0.075/1M input tokens, $0.30/1M output tokens)
- Context window: 1,000,000 tokens
- Rate limit: 1,500 requests/minute

**Free Tier:** 15 requests/minute free, sufficient for initial testing

---

### 2. Anthropic Claude API (Primary for Article Generation)

**Purpose:** Article generation with best long-form Indonesian writing quality

**Steps:**
1. Go to https://console.anthropic.com/
2. Sign in or create account
3. Navigate to API Keys section
4. Create API key
5. Copy the API key to `.env` as `ANTHROPIC_API_KEY`

**Configuration:**
- Primary model: claude-3-5-sonnet-20241022 ($3.00/1M input tokens, $15.00/1M output tokens)
- Context window: 200,000 tokens
- Rate limit: 50 requests/minute

**Free Tier:** Limited free credits, good for initial testing

---

### 3. OpenAI API (Fallback for Embeddings & LLM)

**Purpose:** Text embeddings (text-embedding-3-small) and fallback LLM

**Steps:**
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Navigate to API Keys section
4. Create new secret key
5. Copy the API key to `.env` as `OPENAI_API_KEY`

**Configuration:**
- Embedding model: text-embedding-3-small ($0.13/1M tokens)
- Fallback model: gpt-4o ($2.50/1M input tokens, $10.00/1M output tokens)
- Rate limit: 3,000 RPM

**Free Tier:** $5 free credits, sufficient for initial testing

---

### 4. Google Cloud Speech-to-Text (Fallback for Extraction)

**Purpose:** Fallback STT API when YouTube subtitles not available

**Steps:**
1. Go to https://console.cloud.google.com/
2. Create project or select existing project
3. Enable Cloud Speech-to-Text API
4. Create service account key
5. Download JSON credentials file
6. Save to `./infrastructure/secrets/gcp-credentials.json`
7. Set `GOOGLE_APPLICATION_CREDENTIALS=./infrastructure/secrets/gcp-credentials.json` in `.env`

**Configuration:**
- Rate limit: 60 requests/minute
- Cost: $0.006/15 seconds

**Free Tier:** 60 minutes/month free

---

### 5. AssemblyAI API (Alternative STT)

**Purpose:** Alternative STT API if Google Cloud STT unavailable

**Steps:**
1. Go to https://www.assemblyai.com/
2. Sign in or create account
3. Navigate to API Keys section
4. Create API key
5. Copy the API key to `.env` as `ASSEMBLYAI_API_KEY`

**Configuration:**
- Rate limit: 100 requests/minute
- Cost: $0.015/minute

**Free Tier:** Limited free transcription hours

---

## Configuration File Setup

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` and replace placeholder values with actual API keys

3. Ensure `.env` is added to `.gitignore` (security requirement)

4. Restart services to load new configuration

---

## Cost Estimation

Based on PRD v2.0 targets (50 videos/day):

**Enrichment (per video):**
- Gemini 1.5 Flash: ~$0.003-$0.01 per video
- Daily enrichment cost: ~$0.15-$0.50

**Article Generation (per video):**
- Claude 3.5 Sonnet: ~$0.20-$0.40 per video
- Daily article cost: ~$10.00-$20.00 (assuming 20-50 articles/day)

**Total Daily Cost:** ~$10.15-$20.50
**Total Monthly Cost:** ~$300-$600

---

## Security Best Practices

1. **Never commit `.env` file to version control**
2. **Rotate API keys every 90 days** (per PRD requirements)
3. **Use different API keys for development and production**
4. **Monitor API usage and costs** (cost tracking implemented in `ai.cost_tracking`)
5. **Implement rate limiting** to prevent quota exhaustion
6. **Set daily cost limits** to prevent unexpected overages

---

## Testing API Connectivity

After configuring API keys, test connectivity with:

```bash
# Test environment loading
python3 -c "from ai_shared.config import ServiceConfig; config = ServiceConfig(); print('Gemini API Key:', config.gemini_api_key[:10] + '...' if config.gemini_api_key else 'Not configured')"

# Test API connection (example for enrichment service)
python3 scripts/test_api_connectivity.py
```
"""
    
    return guide_content


def main():
    """Generate configuration files and setup guide."""
    
    print("=" * 70)
    print("🔧 GENERATING CONFIGURATION FILES")
    print("=" * 70)
    print()
    
    # Create .env template
    env_template = generate_env_template()
    env_file = Path("/home/sdibonerate85/Developmet/living-atlas/ai-platform/.env.enrichment")
    with open(env_file, 'w') as f:
        f.write(env_template)
    print(f"✅ Generated: {env_file}")
    
    # Generate setup guide
    setup_guide = generate_api_setup_guide()
    guide_file = Path("/home/sdibonerate85/Developmet/living-atlas/ai-platform/docs/API_SETUP_GUIDE.md")
    guide_file.parent.mkdir(exist_ok=True, parents=True)
    with open(guide_file, 'w') as f:
        f.write(setup_guide)
    print(f"✅ Generated: {guide_file}")
    
    print()
    print("=" * 70)
    print("✅ CONFIGURATION FILES GENERATED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Generated files:")
    print(f"  📄 {env_file}")
    print(f"  📄 {guide_file}")
    print()
    print("Next steps:")
    print("  1. Copy .env.enrichment to .env: cp .env.enrichment .env")
    print("  2. Edit .env and add your actual API keys")
    print("  3. Follow API setup guide to obtain keys")
    print("  4. Test API connectivity")
    print("  5. Set up Redpanda and Redis")


if __name__ == "__main__":
    main()