# AI Pipeline PRD

## Version 1.0
## Status: Draft

---

# Overview

The AI Pipeline is the intelligence layer of The Living Atlas. It transforms raw multimedia content (YouTube videos, podcasts, audio) into structured knowledge: stories, entities, themes, motifs, claims, and articles.

The AI pipeline operates asynchronously, triggered by domain events from the content-service and publishing results back as domain events consumed by the knowledge-service.

---

# Architecture

```
Content Source (YouTube/Podcast)
    ↓
Ingestion Service (Python, YT-DLP)
    ↓ Raw audio/video + metadata
Extraction Service (Python, WhisperX, Pyannote)
    ↓ Transcript + Speaker Diarization
Enrichment Service (Python, LLMs)
    ↓ Knowledge Extraction (entities, themes, claims)
    ↓
┌──────────────────────────────────────────┐
│         Parallel Processing              │
│                                          │
│  Embedding Service ──→ Weaviate Sync     │
│  Article Service   ──→ Article Storage   │
│  KG Sync           ──→ Neo4j Graph       │
└──────────────────────────────────────────┘
```

---

# AI Services

## 1. Ingestion Service

**Purpose**: Acquire multimedia content from external sources.

**Language**: Python 3.14

**Key Dependencies**: YT-DLP, FFmpeg, httpx, aiohttp

### Workflow
1. Receive `ChannelRegistered` event from content-service
2. Crawl channel/playlist metadata
3. Download video metadata (no video download initially)
4. Extract available subtitles
5. Store raw metadata JSON in `source.video_payload_versions`
6. If subtitles available, store in `source.subtitle_tracks`
7. If no subtitles, flag for audio extraction

### Inputs
| Input | Source | Format |
|-------|--------|--------|
| Channel ID | content-service | UUID |
| Video URL | content-service | String |
| Platform | content-service | Enum (youtube, spotify, etc.) |

### Outputs
| Output | Destination | Format |
|--------|-------------|--------|
| Video metadata | source.video_payload_versions | JSONB |
| Audio file | source.assets | Storage path |
| Subtitle tracks | source.subtitle_tracks | VTT/SRT |

### Performance Targets
- Channel crawl: < 30s for 100 videos
- Single video metadata: < 5s
- Audio extraction: < 2x video duration

---

## 2. Extraction Service

**Purpose**: Transcribe audio to text with speaker diarization.

**Language**: Python 3.14

**Key Dependencies**: WhisperX, Pyannote-audio, torch

### Workflow
1. Receive audio file path from ingestion or subtitle trigger
2. Run WhisperX for transcription (speech-to-text)
3. Run Pyannote for speaker diarization (who spoke when)
4. Align transcript with speaker labels
5. Split into segments (by sentence or time boundary)
6. Store transcripts and segments in source.transcripts and source.transcript_segments
7. Emit `TranscriptImported` event

### Processing Modes
| Mode | Description | Quality | Speed |
|------|-------------|---------|-------|
| `whisperx` | Full WhisperX transcription | Highest | Slowest |
| `subtitle` | Use existing subtitles | High | Fast |
| `auto_subtitle` | YouTube auto-generated | Medium | Fastest |

### Inputs
| Input | Source | Format |
|-------|--------|--------|
| Audio file | source.assets | WAV/MP3 |
| Video ID | content-service | UUID |
| Language | content-service | ISO code |

### Outputs
| Output | Destination | Format |
|--------|-------------|--------|
| Full transcript | source.transcripts | Text + metadata |
| Segments | source.transcript_segments | Timestamped text |
| Speakers | source.speakers | Speaker labels |
| Speaker-segment mapping | source.transcript_segments | speaker_id per segment |

### Performance Targets
- 10-min audio: < 5 min processing
- 60-min audio: < 20 min processing (with GPU)

---

## 3. Enrichment Service

**Purpose**: Extract structured knowledge from transcripts.

**Language**: Python 3.14

**Key Dependencies**: LangChain, OpenAI SDK, Anthropic SDK, Gemini SDK

### Workflow
1. Receive `TranscriptImported` event
2. For each transcript segment, run extraction pipeline:

```
Segment Text
    ↓
Entity Extraction → Who/what is mentioned?
    ↓
Theme Classification → What themes are present?
    ↓
Motif Identification → What narrative motifs?
    ↓
Claim Extraction → What specific claims?
    ↓
Cultural Context → What culture/culture elements?
```

3. Aggregate results across segments for story-level extraction
4. Create knowledge objects, themes, motifs, claims
5. Emit `EnrichmentJobCompleted` event

### Extraction Categories

#### Entity Extraction
| Entity Type | Example | Description |
|-------------|---------|-------------|
| Spirit/K ghost | Kuntilanak, Pocong, Genderuwo | Supernatural entities |
| Person | Nadia Omara, Risa | Real people mentioned |
| Location | Pontianak, Gunung Lawu | Geographic locations |
| Ritual | Ruwatan, Selamatan | Cultural practices |
| Belief | Ancestor worship, Kejawen | Belief systems |

#### Theme Classification
| Theme | Description |
|-------|-------------|
| Fear | Stories centered on fear |
| Loss | Stories about losing something/someone |
| Afterlife | Death and beyond |
| Curiosity | Exploration of the unknown |
| Forbidden Place | Taboo locations |
| Ancestral Spirits | Connection to ancestors |

#### Motif Identification
| Motif | Description |
|-------|-------------|
| Mysterious Voice | Unexplained sounds |
| Shadow Figure | Dark shape sightings |
| Abandoned House | Haunted building |
| Sacred Tree | Spirit-inhabited tree |
| Possession | Spiritual possession |

### LLM Strategy
| Task | Primary Model | Fallback | Context Window |
|------|---------------|----------|---------------|
| Entity Extraction | Claude 3.5 Sonnet | Gemini 1.5 Pro | 8K tokens |
| Theme Classification | Claude 3 Haiku | GPT-4o Mini | 4K tokens |
| Motif Identification | Claude 3 Haiku | GPT-4o Mini | 4K tokens |
| Claim Extraction | Claude 3.5 Sonnet | Gemini 1.5 Pro | 8K tokens |
| Story Synthesis | Claude 3 Opus | GPT-4o | 32K tokens |

### Performance Targets
- Segment processing: < 5s per segment
- Full video (100 segments): < 10 min
- Batch mode: 50 segments/min with parallel LLM calls

---

## 4. Embedding Service

**Purpose**: Generate vector embeddings for semantic search.

**Language**: Python 3.14

**Key Dependencies**: OpenAI Embeddings API, sentence-transformers, weaviate-client

### Workflow
1. Receive enrichment results
2. Generate embeddings for:
   - Transcript segments
   - Knowledge objects
   - Stories
   - Themes and motifs
3. Store embeddings in weaviate
4. Emit `EmbeddingCreated` event

### Embedding Strategy
| Content Type | Dimensions | Model | Chunk Size |
|-------------|-----------|-------|------------|
| Transcript segment | 1536 | text-embedding-3-small | 512 tokens |
| Story | 1536 | text-embedding-3-small | Full story |
| Knowledge object | 1536 | text-embedding-3-small | Full object |
| Theme/Motif | 1536 | text-embedding-3-small | Description |

### Parallelization
- Batch embeddings: 20 texts per request
- Concurrent requests: 10 (rate limited)
- Estimated: 200 segments = ~30 seconds

---

## 5. Article Service

**Purpose**: Generate human-quality articles from extracted knowledge.

**Language**: Python 3.14

**Key Dependencies**: LangChain, LLM SDKs, Jinja2 templates

### Article Types
| Type | Style | Source | Use Case |
|------|-------|--------|----------|
| Narrative | Story-telling, journalistic | Story + transcript | Public articles |
| Knowledge | Structured, research-focused | Knowledge objects | Reference articles |
| News | Journalistic, factual | Recent events | News coverage |
| Creative | Opinion, speculative | Extracted themes | Studio content |

### Workflow
1. Receive enrichment results for a story
2. Select article type based on configuration
3. Build prompt with:
   - Story narrative
   - Extracted entities, themes, motifs
   - Transcript evidence (quotations)
   - Cultural context
   - Writing style guidelines
4. Generate article via LLM
5. Store as draft in content.articles
6. Emit `ArticleGenerated` event

### Quality Rules
- Narrative articles must cite source transcript segments
- Knowledge articles must reference knowledge objects
- AI-generated articles are tagged with `generated_by: "ai"` and `model_version`
- Minimum 1000 characters for published articles

---

## 6. Orchestration Service

**Purpose**: Coordinate the AI pipeline execution.

**Language**: Python 3.14

**Key Dependencies**: Celery, Redis, httpx

### Responsibilities
1. **Pipeline orchestration**: Define and execute processing workflows
2. **Queue management**: Prioritize and queue pipeline jobs
3. **Retry logic**: Exponential backoff for failed steps
4. **Scheduling**: Periodic crawling and reprocessing
5. **Monitoring**: Track pipeline health and performance

### Pipeline Definitions

#### Full Pipeline (YouTube video)
```
Ingestion → Extraction → Enrichment → Embedding → Article
```

#### Metadata-only Pipeline (Podcast RSS)
```
Ingestion → Enrichment (metadata only) → Embedding
```

#### Reprocessing Pipeline (existing transcript)
```
Enrichment → Embedding → Article
```

### Retry Policy
| Attempt | Delay | Notes |
|---------|-------|-------|
| 1 | 0s | Immediate |
| 2 | 30s | Transient error recovery |
| 3 | 5 min | Resource contention wait |
| 4 | 30 min | Extended outage |
| 5 | 2 hours | Final attempt |
| 6+ | Manual | Admin intervention required |

---

# Pipeline Event Flow

```
1. content-service: ChannelRegistered
2. ingestion-service: VideoIngested
3. ingestion-service: MetadataCaptured
4. extraction-service: TranscriptImported
5. extraction-service: TranscriptSegmentCreated
6. enrichment-service: EnrichmentJobCompleted
   └── Creates: KnowledgeObjectCreated, ThemeExtracted, MotifExtracted, ClaimCreated
7. embedding-service: EmbeddingCreated
8. article-service: ArticleGenerated
9. orchestration-service: PipelineCompleted
```

---

# Data Contracts

## Event: EnrichmentResult
```json
{
  "sourceId": "uuid",
  "videoId": "uuid",
  "transcriptId": "uuid",
  "segments": [
    {
      "segmentId": "uuid",
      "startSeconds": 125.5,
      "endSeconds": 135.2,
      "text": "In Pontianak, they say Kuntilanak...",
      "speakerId": "uuid",
      "entities": [
        {"name": "Kuntilanak", "type": "spirit", "confidence": 0.95}
      ],
      "themes": ["Fear", "Supernatural"],
      "motifs": ["Mysterious Voice"],
      "claims": [
        {"text": "Kuntilanak appears near banana trees", "confidence": 0.85}
      ]
    }
  ],
  "story": {
    "title": "The Kuntilanak of Pontianak",
    "summary": "A traditional folklore...",
    "type": "folklore",
    "confidence": 0.88
  },
  "metadata": {
    "modelName": "claude-3.5-sonnet",
    "modelVersion": "20241022",
    "processingTime": 45.2,
    "tokenCount": 4560
  }
}
```

---

# Performance & Scaling

## Estimated Processing Times
| Video Length | Ingestion | Extraction | Enrichment | Embedding | Article | Total |
|-------------|-----------|------------|------------|-----------|---------|-------|
| 10 min | 30s | 5 min | 2 min | 10s | 30s | ~8 min |
| 30 min | 60s | 15 min | 5 min | 20s | 45s | ~22 min |
| 60 min | 120s | 20 min | 10 min | 30s | 60s | ~33 min |
| 120 min | 180s | 40 min | 20 min | 60s | 90s | ~64 min |

## Scaling Strategy
1. **Horizontal scaling**: Multiple workers per service
2. **Job priority**: User-requested > system-triggered > batch
3. **Resource isolation**: GPU workers for extraction, CPU for enrichment
4. **Queue depth monitoring**: Alert if > 1000 pending jobs

---

# Monitoring & Alerting

## Key Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Pipeline success rate | > 95% | < 90% |
| Average processing time | < 30 min | > 60 min |
| Queue depth | < 100 | > 500 |
| LLM API error rate | < 1% | > 5% |
| Embedding generation rate | > 100/min | < 50/min |

---

# References

- ADR-009: AI Pipeline Integration Pattern
- plan.md - AI Platform
- BACKEND-PRD.md §4 AI Integration Requirements
- ai-platform/PRD.md - Existing AI Platform PRD