#!/usr/bin/env python3
"""Redpanda topic setup for AI Platform event-driven architecture.

Creates all topics defined in the queue contract specification.
Reference: docs/ai-platform/queue-contract-specification.md
"""

import subprocess
from pathlib import Path


def create_redpanda_topics():
    """Create required Redpanda topics for pipeline events."""
    
    # Standard topics matching EventTopics.java and queue-contract-specification.md
    topics = [
        # Source topics
        {"name": "source.submitted", "retention": "7D", "partitions": 3},
        {"name": "source.metadata.imported", "retention": "7D", "partitions": 3},
        
        # Transcript topics
        {"name": "transcript.imported", "retention": "7D", "partitions": 3},
        {"name": "transcript.normalized", "retention": "7D", "partitions": 3},
        
        # Story topics
        {"name": "story.extraction.requested", "retention": "7D", "partitions": 6},
        {"name": "story.extracted", "retention": "7D", "partitions": 3},
        
        # Knowledge topics
        {"name": "knowledge.extraction.requested", "retention": "7D", "partitions": 6},
        {"name": "knowledge.extracted", "retention": "7D", "partitions": 3},
        {"name": "knowledge.normalization.requested", "retention": "7D", "partitions": 3},
        {"name": "knowledge.normalized", "retention": "7D", "partitions": 3},
        {"name": "knowledge.validation.requested", "retention": "7D", "partitions": 3},
        {"name": "knowledge.validated", "retention": "7D", "partitions": 3},
        
        # Article topics
        {"name": "article.generation.requested", "retention": "7D", "partitions": 3},
        {"name": "article.generated", "retention": "7D", "partitions": 3},
        
        # Embedding topics
        {"name": "embedding.generation.requested", "retention": "7D", "partitions": 3},
        {"name": "embedding.generated", "retention": "7D", "partitions": 3},
        
        # Graph projection topics
        {"name": "graph.projection.requested", "retention": "7D", "partitions": 3},
        {"name": "graph.projected", "retention": "7D", "partitions": 3},
        
        # Review topics (compacted)
        {"name": "review.requested", "retention": "7D", "partitions": 3},
        {"name": "review.approved", "retention": "7D", "partitions": 3},
        {"name": "review.rejected", "retention": "7D", "partitions": 3},
        
        # Publication topics
        {"name": "publication.requested", "retention": "7D", "partitions": 3},
        {"name": "publication.completed", "retention": "7D", "partitions": 3},
        
        # Pipeline failure topic
        {"name": "pipeline.failed", "retention": "30D", "partitions": 1},
    ]
    
    print("=" * 70)
    print("🔧 REDPANDA TOPIC SETUP")
    print("=" * 70)
    print()
    
    for topic in topics:
        print(f"Creating topic: {topic['name']}")
        print(f"  Retention: {topic['retention']}")
        print(f"  Partitions: {topic['partitions']}")
        print()
        
        # Use rpk command to create topic
        cmd = [
            "rpk", "topic", "create", topic["name"],
            "--partitions", str(topic["partitions"]),
            "--replication-factor", "3",
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"  ✅ Created: {topic['name']}")
            else:
                if "ALREADY_EXISTS" in result.stderr:
                    print(f"  ⚠️  Already exists: {topic['name']}")
                else:
                    print(f"  ❌ Failed: {result.stderr}")
        except FileNotFoundError:
            print(f"  ⚠️  rpk not found. Run manually: {' '.join(cmd)}")
        
        print()
    
    print("=" * 70)
    print("✅ Topic setup complete")
    print("=" * 70)


if __name__ == "__main__":
    create_redpanda_topics()