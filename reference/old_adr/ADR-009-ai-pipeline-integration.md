# ADR-009: AI Pipeline Integration Pattern

## Status
Accepted

## Context
AI processing (transcription, knowledge extraction, article generation) involves long-running, resource-intensive operations. These cannot be handled synchronously within Spring Boot services. Python is the preferred language for AI/ML workloads.

## Decision
AI services run as separate Python services outside the Spring Boot monolith. Communication uses asynchronous job queues and REST for control operations.

## Rationale
- **Language fit**: Python has superior AI/ML library ecosystem (WhisperX, Pyannote, LangChain)
- **Resource isolation**: AI workloads (GPU, large memory) must not impact API responsiveness
- **Independent scaling**: AI services scale differently than API services
- **Failure isolation**: A crash in AI pipeline does not affect API availability

## Architecture
```
Spring Boot Services
    ↓ HTTP (control) / Events (trigger)
Job Queue (Transactional Outbox → Redpanda)
    ↓
AI Platform (Python services)
    ↓ HTTP / Events
Spring Boot Services
```

## AI Service Responsibilities
| Service | Language | Responsibility |
|---------|----------|---------------|
| ingestion-service | Python | YouTube crawl, channel/playlist/video acquisition |
| extraction-service | Python | WhisperX transcription, Pyannote speaker diarization |
| enrichment-service | Python | Theme, motif, entity extraction via LLMs |
| embedding-service | Python | Vector embedding generation, Weaviate sync |
| article-service | Python | Narrative/knowledge/news article generation |
| orchestration-service | Python | Pipeline orchestration, retry, queue management |

## Communication Contract
1. Spring Boot publishes event → AI service consumes
2. AI service processes (potentially minutes/hours)
3. AI service publishes result event → Spring Boot consumes
4. Status updates via polling or callback events

## References
- plan.md - AI Platform
- BACKEND-PRD.md §4 AI Integration Requirements