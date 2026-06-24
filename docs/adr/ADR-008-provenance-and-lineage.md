# ADR-008: Provenance and Data Lineage

## Status
Accepted

## Context
For anthropological and research integrity, every knowledge object must be traceable to its original source. AI-generated content and human-edited content must be distinguishable. Contradicting claims across sources must be preserved, not reconciled.

## Decision
All knowledge objects must maintain complete provenance chains from source to derived artifact. Claims are stored independently from facts, and contradictions are explicitly modeled.

## Rationale
- **Research integrity**: Anthropologists need source traceability
- **AI governance**: AI-generated content must be identifiable
- **Contradiction preservation**: Folklore inherently has conflicting versions
- **Audit compliance**: Every change must be attributable

## Provenance Chain
```
Source (Video/Podcast/Book)
  ↓ Original Content
Transcript
  ↓ Segment Extraction  
Transcript Segment
  ↓ Evidence Link
Story / Claim / Knowledge Object
  ↓ Human or AI Review
Reviewed / Verified Content
```

## Implementation
1. **evidence_level** enum tracks derivation: direct, derived, inferred, generated
2. **claim_sources** table links claims to transcript segments with confidence scores
3. **contradictions** table explicitly models conflicting versions
4. **lineage** table tracks all cross-entity relationships
5. AI-generated content is tagged with `extraction_method` and `model_version`

## Governance Rules
- Sources are never deleted (immutable acquisition)
- Transcripts are versioned (immutable versions)
- Knowledge objects use soft delete with audit trail
- Contradictions are never resolved; multiple versions coexist
- AI extraction confidence scores must be preserved

## References
- ddl.md - Source Ingestion Domain, Knowledge Intelligence Layer
- BACKEND-PRD.md §3 Source Domain, §7 Audit Requirements