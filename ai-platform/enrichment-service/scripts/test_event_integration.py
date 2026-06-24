#!/usr/bin/env python3
"""Test script to demonstrate enrichment-service event integration flow.

This script shows how events flow through the enrichment service:
1. TranscriptGenerated event triggers enrichment
2. Enrichment processes the transcript
3. KnowledgeExtracted event is produced on completion
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
import sys

# Add shared package to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared" / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_shared.events import TranscriptGenerated, KnowledgeExtracted
from enrichment.application.service import EnrichmentService, EnrichmentOutput


async def demonstrate_event_flow():
    """Demonstrate the complete event flow without actual Kafka."""
    
    print("=" * 70)
    print("🎯 ENRICHMENT SERVICE EVENT FLOW DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Simulate TranscriptGenerated event
    video_id = str(uuid.uuid4())
    transcript_id = str(uuid.uuid4())
    extraction_run_id = str(uuid.uuid4())
    
    print("📥 STEP 1: Receive TranscriptGenerated Event")
    print("-" * 70)
    transcript_event = TranscriptGenerated(
        event_version="2",
        video_id=uuid.UUID(video_id),
        transcript_id=uuid.UUID(transcript_id),
        extraction_run_id=uuid.UUID(extraction_run_id),
        source_type="youtube_subtitle",
        language_detected="id",
        duration_seconds=3531,
        word_count=12000,
        avg_confidence=0.95,
        has_low_confidence_segments=False,
        cost_usd=0.0,
        timestamp=datetime.utcnow(),
    )
    print(f"Event Data:")
    print(f"  video_id: {video_id}")
    print(f"  transcript_id: {transcript_id}")
    print(f"  source_type: {transcript_event.source_type}")
    print(f"  word_count: {transcript_event.word_count}")
    print(f"  avg_confidence: {transcript_event.avg_confidence}")
    print()
    
    # Load clean transcript (using RJL 5 data)
    transcript_file = Path("/tmp/clean_transcript_rjl5.txt")
    if not transcript_file.exists():
        print("⚠️  Clean transcript not found at /tmp/clean_transcript_rjl5.txt")
        print("Using sample transcript for demonstration...")
        transcript_text = "Ini adalah contoh transkrip tentang budaya misteri Indonesia..."
    else:
        with open(transcript_file, 'r') as f:
            transcript_text = f.read()
        
    print(f"📄 Loaded transcript: {len(transcript_text)} characters")
    print()
    
    print("🔄 STEP 2: Process Enrichment")
    print("-" * 70)
    print("Enrichment service will:")
    print("  1. Detect story boundaries in transcript")
    print("  2. Extract themes (e.g., Sacred Time, Cultural Introspection)")
    print("  3. Extract motifs (e.g., Silent Procession, Sacred Journey)")
    print("  4. Extract archetypes (e.g., Guardian Spirit, Seeker)")
    print("  5. Extract entities (e.g., Kanjeng Raden Tumenggung, Keraton Yogyakarta)")
    print("  6. Extract claims with evidence linking")
    print("  7. Extract relationships between entities")
    print("  8. Store results in database")
    print("  9. Track costs and metrics")
    print()
    
    # Simulate enrichment output (without actual LLM calls)
    print("📊 Simulated Enrichment Output:")
    print("-" * 70)
    
    enrichment_output = EnrichmentOutput(
        video_id=video_id,
        transcript_id=transcript_id,
        enrichment_run_id=str(uuid.uuid4()),
        themes=[
            {"name": "Sacralization of Time", "confidence": 0.9, "evidence": "malam satu suro adalah malam sakral"},
            {"name": "Cultural Introspection", "confidence": 0.85, "evidence": "introspeksi diri"},
            {"name": "Javanese-Islamic Syncretism", "confidence": 0.8, "evidence": "kalender Jawa menggabungkan tradisi"},
        ],
        motifs=[
            {"name": "Silent Procession", "confidence": 0.88, "evidence": "berjalan tanpa bicara"},
            {"name": "Sacred Journey", "confidence": 0.85, "evidence": "keliling benteng Keraton"},
        ],
        archetypes=[
            {"name": "Guardian Spirit", "confidence": 0.82, "evidence": "roh penjaga Keraton"},
            {"name": "Seeker", "confidence": 0.9, "evidence": "pencari pengetahuan budaya"},
        ],
        entities=[
            {"name": "Kanjeng Raden Tumenggung", "type": "person", "confidence": 0.95, "description": "Cultural authority figure"},
            {"name": "Keraton Yogyakarta", "type": "location", "confidence": 0.98, "description": "Javanese royal palace"},
            {"name": "Malam Satu Suro", "type": "ritual", "confidence": 0.92, "description": "Sacred night in Javanese calendar"},
            {"name": "Mubeng Beteng", "type": "ritual", "confidence": 0.9, "description": "Walking around fortress walls"},
        ],
        claims=[
            {"claim": "Malam satu suro adalah malam sakral bagi masyarakat Jawa", "type": "cultural_belief", "confidence": 0.92, "evidence": "Kanjeng Raden Tumenggung menyatakan..."},
            {"claim": "Mubeng beteng dilakukan tanpa alas kaki", "type": "observation", "confidence": 0.95, "evidence": "peserta berjalan tanpa alas kaki"},
            {"claim": "Ritual ini sebagai sarana introspeksi diri", "type": "interpretation", "confidence": 0.85, "evidence": "maksudnya adalah introspeksi"},
        ],
        relationships=[
            {"source_entity": "Kanjeng Raden Tumenggung", "target_entity": "Keraton Yogyakarta", "relationship_type": "ASSOCIATED_WITH", "confidence": 0.95},
            {"source_entity": "Mubeng Beteng", "target_entity": "Malam Satu Suro", "relationship_type": "PART_OF", "confidence": 0.98},
        ],
        story_boundaries=[
            {"boundary_start": 0, "boundary_end": 12000, "story_type": "introduction", "confidence": 0.85},
        ],
        total_cost_usd=0.045,
        total_duration_ms=12300,
        total_tokens=42000,
    )
    
    print(f"Enrichment Run ID: {enrichment_output.enrichment_run_id}")
    print(f"Themes Extracted: {len(enrichment_output.themes)}")
    print(f"Motifs Extracted: {len(enrichment_output.motifs)}")
    print(f"Archetypes Extracted: {len(enrichment_output.archetypes)}")
    print(f"Entities Extracted: {len(enrichment_output.entities)}")
    print(f"Claims Extracted: {len(enrichment_output.claims)}")
    print(f"Relationships Extracted: {len(enrichment_output.relationships)}")
    print(f"Total Cost: ${enrichment_output.total_cost_usd:.4f}")
    print(f"Processing Time: {enrichment_output.total_duration_ms:.0f}ms")
    print(f"Total Tokens: {enrichment_output.total_tokens:,}")
    print()
    
    print("📤 STEP 3: Produce KnowledgeExtracted Event")
    print("-" * 70)
    
    knowledge_event = KnowledgeExtracted(
        event_version="1",
        video_id=uuid.UUID(video_id),
        transcript_id=uuid.UUID(transcript_id),
        enrichment_run_id=uuid.UUID(enrichment_output.enrichment_run_id),
        entity_count=len(enrichment_output.entities),
        claim_count=len(enrichment_output.claims),
        theme_count=len(enrichment_output.themes),
        motif_count=len(enrichment_output.motifs),
        story_count=len(enrichment_output.story_boundaries),
        model_used="gemini-1.5-flash",
        cost_usd=enrichment_output.total_cost_usd,
        timestamp=datetime.utcnow(),
    )
    
    print(f"Event Data:")
    print(f"  video_id: {video_id}")
    print(f"  transcript_id: {transcript_id}")
    print(f"  enrichment_run_id: {enrichment_output.enrichment_run_id}")
    print(f"  entity_count: {knowledge_event.entity_count}")
    print(f"  claim_count: {knowledge_event.claim_count}")
    print(f"  theme_count: {knowledge_event.theme_count}")
    print(f"  motif_count: {knowledge_event.motif_count}")
    print(f"  story_count: {knowledge_event.story_count}")
    print(f"  model_used: {knowledge_event.model_used}")
    print(f"  cost_usd: ${knowledge_event.cost_usd:.4f}")
    print()
    
    print("=" * 70)
    print("✅ EVENT FLOW DEMONSTRATION COMPLETE")
    print("=" * 70)
    print()
    print("Summary:")
    print("  📥 Received: ai.transcript.generated.v1")
    print("  🔄 Processed: Enrichment with 6 extractors")
    print("  📤 Produced: ai.knowledge.extracted.v1")
    print()
    print("Actual Implementation (when infrastructure is available):")
    print("  1. EventConsumer listens to ai.transcript.generated.v1")
    print("  2. Handler validates event and retrieves transcript from database")
    print("  3. EnrichmentService.process_transcript() runs all extractors")
    print("  4. Results stored in knowledge schema tables")
    print("  5. EventProducer publishes to ai.knowledge.extracted.v1")
    print("  6. Errors sent to DLQ for retry")
    print()
    print("Next Steps in Pipeline:")
    print("  7. embedding-service consumes ai.knowledge.extracted.v1")
    print("  8. article-service consumes ai.knowledge.extracted.v1")
    print("  9. orchestration-service monitors pipeline health")


if __name__ == "__main__":
    asyncio.run(demonstrate_event_flow())