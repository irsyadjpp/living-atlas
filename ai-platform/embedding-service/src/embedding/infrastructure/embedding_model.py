"""Embedding model wrapper — OpenAI API only.

Updated for PRD v2.0:
- NO local embedding model (sentence-transformers removed)
- OpenAI text-embedding-3-small is the only option
"""

import os
import structlog
from openai import OpenAI

logger = structlog.get_logger(__name__)


class OpenAIEmbeddingModel:
    """OpenAI embedding API wrapper — the only embedding model used.

    text-embedding-3-small: 1536 dimensions, $0.13/1M tokens
    No local model fallback — all embeddings via API.
    """

    def __init__(self, model: str = "text-embedding-3-small"):
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LA_OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimension = 1536  # text-embedding-3-small
        self.model_name = model
        logger.info("openai_embedding_initialized", model=model, dimensions=self.dimension)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts via OpenAI API.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors
        """
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [r.embedding for r in response.data]

    def embed_single(self, text: str) -> list[float]:
        """Generate embedding for a single text string."""
        return self.embed([text])[0]

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        """Embed a list of text chunks and attach vectors.

        Args:
            chunks: List of chunk dicts, each must have 'text' key

        Returns:
            Same chunks with 'vector', 'dimension', 'model_name' added
        """
        texts = [c["text"] for c in chunks]
        vectors = self.embed(texts)
        for chunk, vector in zip(chunks, vectors):
            chunk["vector"] = vector
            chunk["dimension"] = self.dimension
            chunk["model_name"] = self.model_name
        return chunks