"""Weaviate vector store sync — batch upsert embeddings."""

import structlog
from typing import Optional

logger = structlog.get_logger(__name__)


class WeaviateSyncer:
    """Sync embeddings to Weaviate vector store.

    Creates collections if they don't exist and batch upserts
    objects with vectors for semantic search.
    """

    def __init__(self, url: str = "http://localhost:8080"):
        import weaviate
        import weaviate.classes as wvc
        self.client = weaviate.connect_to_local()
        self._ensure_schema()

    def _ensure_schema(self):
        """Create collections if they don't exist."""
        import weaviate.classes as wvc
        collections = ["TranscriptSegment", "Entity", "Story"]
        for name in collections:
            if not self.client.collections.exists(name):
                self.client.collections.create(
                    name=name,
                    vectorizer_config=wvc.Configure.Vectorizer.none(),
                    properties=[
                        wvc.Property(name="text", data_type=wvc.DataType.TEXT),
                        wvc.Property(name="source_id", data_type=wvc.DataType.UUID),
                        wvc.Property(name="metadata", data_type=wvc.DataType.OBJECT),
                    ],
                )
                logger.info("weaviate_collection_created", collection=name)

    def batch_upsert(self, collection: str, objects: list[dict]):
        """Batch upsert objects with vectors into a Weaviate collection."""
        col = self.client.collections.get(collection)
        with col.batch.fixed_size(batch_size=100) as batch:
            for obj in objects:
                batch.add_object(
                    properties={
                        "text": obj.get("text", ""),
                        "source_id": obj.get("source_id", ""),
                        "metadata": obj.get("metadata", {}),
                    },
                    vector=obj.get("vector"),
                )
        logger.info("weaviate_upsert_completed", collection=collection, count=len(objects))

    def search(self, collection: str, query_vector: list[float], limit: int = 10) -> list[dict]:
        """Search Weaviate by vector similarity."""
        col = self.client.collections.get(collection)
        response = col.query.near_vector(near_vector=query_vector, limit=limit)
        return [
            {
                "id": obj.uuid,
                "score": obj.metadata.score if obj.metadata else 0,
                "text": obj.properties.get("text", ""),
                "source_id": obj.properties.get("source_id", ""),
            }
            for obj in response.objects
        ]

    def close(self):
        self.client.close()
        logger.info("weaviate_connection_closed")