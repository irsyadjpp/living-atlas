"""Semantic text chunking with overlap for context preservation.

Updated for PRD v2.0:
- Removed speaker references from chunking
- Simplified for transcript segments without speaker labels
"""

import re
import structlog
from typing import Optional

logger = structlog.get_logger(__name__)


class SemanticChunker:
    """Chunk text by sentences with overlap for context preservation.

    Splits long text into overlapping chunks at sentence boundaries
    to ensure each chunk has meaningful context for embedding.
    """

    def __init__(self, max_chunk_size: int = 512, overlap: int = 50):
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap

    def chunk(self, text: str, metadata: Optional[dict] = None) -> list[dict]:
        """Split text into overlapping chunks at sentence boundaries.

        Args:
            text: The text to chunk
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of dicts: [{text, word_count, chunk_index, metadata}]
        """
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_words = len(sentence.split())
            if current_size + sentence_words > self.max_chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "word_count": current_size,
                    "chunk_index": len(chunks),
                    "metadata": metadata or {},
                })
                # Keep overlap sentences for next chunk
                overlap_words = 0
                overlap_chunk = []
                for s in reversed(current_chunk):
                    sw = len(s.split())
                    if overlap_words + sw > self.overlap:
                        break
                    overlap_chunk.insert(0, s)
                    overlap_words += sw
                current_chunk = overlap_chunk
                current_size = overlap_words

            current_chunk.append(sentence)
            current_size += sentence_words

        # Last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "word_count": current_size,
                "chunk_index": len(chunks),
                "metadata": metadata or {},
            })

        logger.info("chunking_completed", chunks=len(chunks), total_words=sum(c["word_count"] for c in chunks))
        return chunks

    def chunk_transcript_segments(
        self,
        segments: list[dict],
        max_chunk_size: int = 512,
    ) -> list[dict]:
        """Chunk transcript segments into embedding-ready pieces.

        Each segment is a dict with: {start, end, content}
        Groups consecutive segments until max_chunk_size is reached.
        No speaker labels — segments are grouped by content only.
        """
        chunks = []
        current_chunk = []
        current_size = 0
        current_start = 0.0
        current_end = 0.0

        for seg in segments:
            seg_words = len(seg.get("content", "").split())
            if current_size + seg_words > max_chunk_size and current_chunk:
                chunk_text = " ".join(s["content"] for s in current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "word_count": current_size,
                    "chunk_index": len(chunks),
                    "start_seconds": current_start,
                    "end_seconds": current_end,
                    "metadata": {"segment_count": len(current_chunk)},
                })
                current_chunk = []
                current_size = 0

            if not current_chunk:
                current_start = seg.get("start", 0.0)
            current_chunk.append(seg)
            current_size += seg_words
            current_end = seg.get("end", 0.0)

        if current_chunk:
            chunk_text = " ".join(s["content"] for s in current_chunk)
            chunks.append({
                "text": chunk_text,
                "word_count": current_size,
                "chunk_index": len(chunks),
                "start_seconds": current_start,
                "end_seconds": current_end,
                "metadata": {"segment_count": len(current_chunk)},
            })

        return chunks