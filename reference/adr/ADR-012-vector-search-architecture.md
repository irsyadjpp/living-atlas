# ADR-012: Vector Search Architecture — Weaviate as Embedding Projection

# Status

Accepted

# Context

## Business Context

The Living Atlas of Indonesian Mystery Culture enables users to search across stories, articles, entities, and claims using natural language queries. A researcher searching for "cerita tentang hantu perempuan di pemakaman" (stories about female ghosts in cemeteries) should find relevant results even if the exact keywords don't match — because the semantic meaning is captured through vector embeddings.

The platform requires semantic search across multiple content types:

- **Stories**: Full narrative text extracted from transcripts
- **Articles**: Narrative, knowledge, news, and creative articles
- **Entities**: Folklore spirits, creatures, people with descriptions
- **Claims**: Evidence-grounded statements extracted from stories
- **Transcript segments**: Raw source material for provenance tracing

Beyond search, embeddings enable:

- **Story similarity**: "Find stories similar to this one" (Story DNA, Phase 3)
- **Clustering**: Automatic discovery of theme/motif groupings
- **Recommendation**: Suggest related content to readers and researchers
- **Research analytics**: Identify gaps and patterns across the knowledge base

## Technical Context

The platform stack includes PostgreSQL 18 (source of truth, per ADR-001), Weaviate 1.37 (vector projection, read-only), and Redpanda (event backbone, per ADR-003). The architecture principle (PRD §3.4) states: "PostgreSQL is source of truth. Weaviate is a Vector Projection. Applications must never write directly to Weaviate."

The AI Platform's embedding service (Python) generates vectors using provider models (OpenAI text-embedding-3-small primary, Gemini text-embedding-004 fallback, per ADR-009). Embeddings are generated asynchronously after content is approved and published.

Weaviate 1.37 provides:
- **Vector search**: ANN (Approximate Nearest Neighbor) indexing with HNSW algorithm
- **Hybrid search**: Combines vector search with BM25 keyword search
- **Native multi-tenancy**: Tenant-level data isolation built into the API
- **Multi-modal support**: Text, image, and cross-modal vectors (future)
- **CRUD API**: RESTful and GraphQL interfaces for data management

## Constraints

1. **No direct writes to Weaviate**: Domain services must never import Weaviate clients. All vector writes go through the embedding service.

2. **Read-only Weaviate for search services**: Search services read from Weaviate but never write. Weaviate is not a transaction participant.

3. **Rebuildable from PostgreSQL**: The entire Weaviate vector index must be rebuildable from PostgreSQL at any time.

4. **Embedding versioning**: When the embedding model changes (e.g., upgrading from text-embedding-3-small to text-embedding-3-large), all existing embeddings become incompatible with new queries. A reindex is required.

5. **Human review gate**: Only APPROVED or PUBLISHED content is embedded and indexed. REVIEW_REQUIRED content must never appear in search results.

6. **Tenant isolation**: Weaviate's native multi-tenancy isolates vector data per tenant. Global knowledge (tenant_id = NULL) is visible to all tenants.

7. **Eventual consistency**: There is a delay between content publication and embedding availability in Weaviate. This is acceptable for search use cases.

8. **Scalability target**: 100,000 stories, 1,000,000 knowledge objects, 10,000,000 transcript segments, 100,000,000 embeddings.

## Problem Statement

Weaviate stores vector embeddings for semantic search across stories, articles, entities, claims, and transcript segments. Embeddings are generated asynchronously by the AI Platform after content is approved. The vector index must be kept in sync with PostgreSQL, support full rebuilds, handle embedding model version changes (requiring reindexing), maintain tenant isolation through native multi-tenancy, and scale to 100,000,000 embeddings. How do we design a vector search architecture that reliably generates embeddings, syncs to Weaviate, supports hybrid search, manages embedding versioning, and provides observable, rebuildable state?

# Decision

**Weaviate stores vector projections of approved content. Embeddings are generated asynchronously by the embedding service after content is approved and published. The vector projection worker consumes domain events from Redpanda, generates embeddings via the provider abstraction layer, and upserts into Weaviate. The vector index is fully rebuildable from PostgreSQL. Weaviate's native multi-tenancy provides tenant isolation. Embedding model version changes trigger a full reindex.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PostgreSQL 18 (Source of Truth)                       │
│                                                                          │
│  content_stories      │  content_articles      │  knowledge_objects     │
│  content_story_vers.  │  knowledge_claims      │  knowledge_folklore    │
│  content_transcripts  │  (segment-level)       │                        │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Transactional Outbox → Redpanda                                  │   │
│  │  Events: ArticlePublished, StoryPublished,                        │   │
│  │  KnowledgeValidated, EmbeddingGenerationRequested,                │   │
│  │  EmbeddingGenerated, ReindexRequested                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Redpanda (Event Backbone)                             │
│                                                                          │
│  Topics consumed by embedding-service:                                   │
│  - embedding.generation.requested  (trigger embedding generation)       │
│  - content.evt: StoryPublished, ArticlePublished                        │
│  - knowledge.evt: KnowledgeValidated                                    │
│  - workflow.evt: ReviewApproved (gate: only approved content)           │
│  - system.evt: ReindexRequested (trigger full reindex)                  │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Embedding Service (Python)                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Embedding Generator                                             │   │
│  │  ──────────────────                                             │   │
│  │  Consumes events from Redpanda                                  │   │
│  │  Fetches source content from PostgreSQL                          │   │
│  │  Prepares text for embedding (chunking, normalization)           │   │
│  │  Calls AI provider to generate embedding vector                  │   │
│  │  Upserts into Weaviate                                           │   │
│  │  Records embedding metadata in PostgreSQL                        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Embedding Model Registry                                        │   │
│  │  ────────────────────────                                        │   │
│  │  Tracks which embedding model version produced each embedding    │   │
│  │  Manages model upgrades: old embeddings marked stale,            │   │
│  │  new embeddings generated with new model                         │   │
│  │  Supports multiple models simultaneously during migration        │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Reindex Coordinator                                            │   │
│  │  ────────────────────                                           │   │
│  │  Triggers: model upgrade, data corruption recovery,              │   │
│  │  scheduled refresh                                               │   │
│  │  Strategy: delete all embeddings for affected content type,      │   │
│  │  regenerate from PostgreSQL in batches                           │   │
│  │  Batch size: 100 embeddings per batch                            │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     Weaviate 1.37 (Read-Only Vector Projection)           │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Classes (per content type)                                      │   │
│  │  ───────────────────────                                         │   │
│  │                                                                   │   │
│  │  class Story {                                                    │   │
│  │    id: uuid                                                       │   │
│  │    title: text                                                    │   │
│  │    summary: text                                                  │   │
│  │    content: text          // Full story text for embedding        │   │
│  │    narrative_type: string                                         │   │
│  │    language: string                                               │   │
│  │    tenant_id: string     // Weaviate native multi-tenancy         │   │
│  │    version: int                                                   │   │
│  │    embedding_model: string  // Which model produced this vector   │   │
│  │    published_at: date                                             │   │
│  │  }                                                                │   │
│  │  → vectorizer: none  // We provide our own embeddings            │   │
│  │                                                                   │   │
│  │  class Article { ... }                                            │   │
│  │  class Entity { ... }                                             │   │
│  │  class Claim { ... }                                              │   │
│  │  class TranscriptSegment { ... }                                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Hybrid Search Configuration                                     │   │
│  │  ──────────────────────────                                      │   │
│  │                                                                   │   │
│  │  Each class has:                                                  │   │
│  │  - Vector index (HNSW) for semantic search                        │   │
│  │  - Inverted index (BM25) for keyword search                       │   │
│  │  - Hybrid search: alpha parameter balances vector vs keyword      │   │
│  │    (alpha=0 → pure BM25, alpha=1 → pure vector)                  │   │
│  │                                                                   │   │
│  │  Default hybrid config:                                           │   │
│  │  { "alpha": 0.75, "vector": 0.75, "keyword": 0.25 }              │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Multi-Tenancy Configuration                                     │   │
│  │  ──────────────────────────────                                  │   │
│  │                                                                   │   │
│  │  Each class is multi-tenant enabled:                              │   │
│  │  { "multiTenancyConfig": { "enabled": true } }                    │   │
│  │                                                                   │   │
│  │  Queries are scoped to a tenant:                                  │   │
│  │  GET /v1/objects?tenant=T1                                       │   │
│  │                                                                   │   │
│  │  Global knowledge (tenant_id=NULL) is stored in a "global"       │   │
│  │  tenant that all authenticated users can query.                  │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## Detailed Decision Rules

### Rule 1: Event-Driven Embedding Generation

The embedding service consumes domain events and generates embeddings for approved content. Each content type has a dedicated handler.

```python
class EmbeddingService:
    """Generates vector embeddings for approved content and syncs to Weaviate."""
    
    EVENT_HANDLERS = {
        "StoryPublished": handle_story_published,
        "ArticlePublished": handle_article_published,
        "KnowledgeValidated": handle_knowledge_validated,
        "EmbeddingGenerationRequested": handle_embedding_request,
        "ReindexRequested": handle_reindex_request,
    }
    
    # Content type → Weaviate class mapping
    CLASS_MAPPING = {
        "story": "Story",
        "article": "Article",
        "entity": "Entity",
        "claim": "Claim",
        "transcript_segment": "TranscriptSegment",
    }
    
    async def handle_story_published(self, event):
        """Generate embedding for a published story."""
        story = await self._fetch_story(event.data['storyId'])
        tenant_id = str(event.metadata['tenantId'])
        
        # Prepare text for embedding
        text = self._prepare_story_text(story)
        
        # Generate embedding via provider abstraction layer
        provider = await AIProviderFactory.get_provider("embeddings")
        result = await provider.generate_embeddings(text)
        
        if not result.success:
            raise EmbeddingGenerationError(f"Failed to generate embedding: {result.error}")
        
        # Upsert into Weaviate with tenant isolation
        await self._upsert_to_weaviate(
            class_name="Story",
            uuid=story['id'],
            vector=result.data['embedding'],
            properties={
                "title": story['title'],
                "summary": story['summary'],
                "content": text,
                "narrative_type": story['narrative_type'],
                "language": story['language'],
                "tenant_id": tenant_id,
                "version": story['version'],
                "embedding_model": result.data.get('model', 'unknown'),
                "published_at": story['published_at'].isoformat(),
            },
            tenant=tenant_id
        )
        
        # Record embedding metadata in PostgreSQL
        await self._record_embedding_metadata(
            content_type="story",
            content_id=story['id'],
            model=result.data.get('model', 'unknown'),
            dimensions=len(result.data['embedding']),
            version=story['version'],
            tenant_id=tenant_id
        )
    
    def _prepare_story_text(self, story: dict) -> str:
        """Prepare story text for embedding.
        
        Concatenates key fields with clear section markers
        to produce a single text block for embedding.
        """
        parts = [
            f"Title: {story['title']}",
            f"Summary: {story['summary']}",
            f"Narrative: {story.get('content', '')}",
        ]
        if story.get('cultural_context'):
            parts.append(f"Cultural Context: {json.dumps(story['cultural_context'])}")
        
        return "\n\n".join(parts)
```

### Rule 2: Weaviate Class Schema

Each content type has a corresponding Weaviate class. Classes use `vectorizer: none` because embeddings are generated externally by the AI Platform.

```python
WEAVIATE_SCHEMA = {
    "classes": [
        {
            "class": "Story",
            "description": "Published stories with semantic embeddings",
            "vectorizer": "none",  # External embeddings
            "multiTenancyConfig": {"enabled": True},
            "properties": [
                {"name": "title", "dataType": ["text"], "description": "Story title"},
                {"name": "summary", "dataType": ["text"], "description": "Story summary"},
                {"name": "content", "dataType": ["text"], "description": "Full story text"},
                {"name": "narrative_type", "dataType": ["string"]},
                {"name": "language", "dataType": ["string"]},
                {"name": "tenant_id", "dataType": ["string"]},
                {"name": "version", "dataType": ["int"]},
                {"name": "embedding_model", "dataType": ["string"]},
                {"name": "published_at", "dataType": ["date"]},
            ],
            "vectorIndexConfig": {
                "distance": "cosine",
                "efConstruction": 128,
                "ef": -1,  # Dynamic ef at query time
                "maxConnections": 64,
            },
            "invertedIndexConfig": {
                "bm25": {"b": 0.75, "k1": 1.2},
                "stopwords": {"preset": "en"},
            },
        },
        {
            "class": "Article",
            "description": "Published articles with semantic embeddings",
            "vectorizer": "none",
            "multiTenancyConfig": {"enabled": True},
            "properties": [
                {"name": "title", "dataType": ["text"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "article_type", "dataType": ["string"]},  # narrative, knowledge, news, creative
                {"name": "language", "dataType": ["string"]},
                {"name": "tenant_id", "dataType": ["string"]},
                {"name": "version", "dataType": ["int"]},
                {"name": "embedding_model", "dataType": ["string"]},
                {"name": "published_at", "dataType": ["date"]},
            ],
            "vectorIndexConfig": {"distance": "cosine"},
        },
        {
            "class": "Entity",
            "description": "Knowledge objects (spirits, creatures, people) with embeddings",
            "vectorizer": "none",
            "multiTenancyConfig": {"enabled": True},
            "properties": [
                {"name": "name", "dataType": ["text"]},
                {"name": "normalized_name", "dataType": ["text"]},
                {"name": "description", "dataType": ["text"]},
                {"name": "entity_type", "dataType": ["string"]},
                {"name": "subtype", "dataType": ["string"]},
                {"name": "tenant_id", "dataType": ["string"]},
                {"name": "embedding_model", "dataType": ["string"]},
            ],
            "vectorIndexConfig": {"distance": "cosine"},
        },
        {
            "class": "Claim",
            "description": "Evidence-grounded claims with semantic embeddings",
            "vectorizer": "none",
            "multiTenancyConfig": {"enabled": True},
            "properties": [
                {"name": "statement", "dataType": ["text"]},
                {"name": "category", "dataType": ["string"]},
                {"name": "confidence", "dataType": ["number"]},
                {"name": "tenant_id", "dataType": ["string"]},
                {"name": "embedding_model", "dataType": ["string"]},
            ],
            "vectorIndexConfig": {"distance": "cosine"},
        },
        {
            "class": "TranscriptSegment",
            "description": "Transcript segments for provenance-based semantic search",
            "vectorizer": "none",
            "multiTenancyConfig": {"enabled": True},
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "segment_index", "dataType": ["int"]},
                {"name": "speaker", "dataType": ["string"]},
                {"name": "language", "dataType": ["string"]},
                {"name": "tenant_id", "dataType": ["string"]},
                {"name": "embedding_model", "dataType": ["string"]},
            ],
            "vectorIndexConfig": {"distance": "cosine"},
        },
    ]
}
```

### Rule 3: Hybrid Search Configuration

Weaviate's hybrid search combines vector similarity (semantic) with BM25 (keyword) search. The `alpha` parameter controls the balance.

```python
class HybridSearchService:
    """Performs hybrid search across Weaviate classes."""
    
    # Default alpha values per content type
    # alpha=0 → pure BM25 keyword search
    # alpha=1 → pure vector semantic search
    DEFAULT_ALPHA = {
        "story": 0.75,        # Semantic-heavy: story meaning matters most
        "article": 0.70,      # Slightly more keyword for article titles
        "entity": 0.80,       # Very semantic: entity descriptions
        "claim": 0.65,        # Balanced: exact claim text + meaning
        "transcript_segment": 0.60,  # More keyword: exact quote matching
    }
    
    async def hybrid_search(
        self,
        query: str,
        content_types: list[str],
        tenant_id: str,
        limit: int = 20,
        alpha: Optional[float] = None,
        filters: Optional[dict] = None,
    ) -> list[SearchResult]:
        """Perform hybrid search across specified content types.
        
        Args:
            query: Natural language search query
            content_types: List of Weaviate class names to search
            tenant_id: Tenant scope for multi-tenancy
            limit: Max results per content type
            alpha: Hybrid search balance (0=keyword, 1=semantic)
            filters: Additional property filters (e.g., language, entity_type)
        
        Returns:
            Combined, ranked search results
        """
        all_results = []
        
        for class_name in content_types:
            alpha_value = alpha or self.DEFAULT_ALPHA.get(class_name.lower(), 0.75)
            
            # Build the GraphQL hybrid search query
            where_clause = self._build_where_clause(filters, tenant_id)
            
            result = await self.weaviate_client.query.get(
                class_name,
                ["title", "summary", "content", "tenant_id", 
                 "embedding_model", "_additional { distance }"]
            ).with_hybrid(
                query=query,
                alpha=alpha_value,
                properties=["title^2", "summary^1.5", "content^1"]
                # title gets 2x weight, summary 1.5x, content 1x
            ).with_where(where_clause).with_limit(limit).do()
            
            if result and 'data' in result and 'Get' in result['data']:
                items = result['data']['Get'][class_name]
                for item in items:
                    item['_content_type'] = class_name
                    item['_search_type'] = 'hybrid'
                    item['_alpha'] = alpha_value
                all_results.extend(items)
        
        # Sort by distance (closest first) and return
        all_results.sort(key=lambda x: x.get('_additional', {}).get('distance', 1.0))
        return all_results[:limit]
    
    async def pure_vector_search(
        self,
        query: str,
        content_type: str,
        tenant_id: str,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Pure vector (semantic) search — alpha=1.0."""
        return await self.hybrid_search(
            query=query,
            content_types=[content_type],
            tenant_id=tenant_id,
            limit=limit,
            alpha=1.0
        )
    
    async def pure_keyword_search(
        self,
        query: str,
        content_type: str,
        tenant_id: str,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Pure BM25 (keyword) search — alpha=0.0."""
        return await self.hybrid_search(
            query=query,
            content_types=[content_type],
            tenant_id=tenant_id,
            limit=limit,
            alpha=0.0
        )
```

### Rule 4: Embedding Versioning and Model Registry

When the embedding model changes, existing embeddings become incompatible with new queries. The embedding model registry tracks which model produced each embedding and manages migrations.

```sql
CREATE TABLE embedding_model_registry (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    model_name          VARCHAR(100) NOT NULL,   -- 'text-embedding-3-small', 'text-embedding-3-large'
    model_version       VARCHAR(50) NOT NULL,    -- '1', '2', or provider version
    dimensions          INTEGER NOT NULL,         -- 1536, 3072, etc.
    
    -- Lifecycle
    status              VARCHAR(50) NOT NULL DEFAULT 'active',
    -- 'active' → 'deprecated' → 'archived'
    
    -- Migration
    replaced_by         UUID REFERENCES embedding_model_registry(id),
    migration_complete  BOOLEAN NOT NULL DEFAULT false,
    
    -- Metadata
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    activated_at        TIMESTAMPTZ,
    deprecated_at       TIMESTAMPTZ,
    
    UNIQUE(model_name, model_version)
);

CREATE TABLE embedding_metadata (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Content identification
    content_type        VARCHAR(50) NOT NULL,     -- 'story', 'article', 'entity', 'claim', 'transcript_segment'
    content_id          UUID NOT NULL,
    
    -- Embedding details
    model_id            UUID NOT NULL REFERENCES embedding_model_registry(id),
    dimensions          INTEGER NOT NULL,
    content_version     BIGINT NOT NULL,          -- Version of source content when embedded
    
    -- Status
    is_current          BOOLEAN NOT NULL DEFAULT true,
    -- false when a newer model has produced a replacement embedding
    
    -- Timing
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(content_type, content_id, model_id)
);

CREATE INDEX idx_embedding_current ON embedding_metadata(content_type, content_id) 
    WHERE is_current = true;
```

**Model upgrade flow**:

```python
class EmbeddingModelUpgrader:
    """Manages embedding model upgrades with zero downtime."""
    
    async def upgrade_model(
        self,
        new_model_name: str,
        new_model_version: str,
        new_dimensions: int,
    ):
        """Upgrade to a new embedding model.
        
        Process:
        1. Register new model (status = 'active')
        2. New content uses new model immediately
        3. Background job regenerates embeddings for existing content
        4. Old model marked 'deprecated' when migration complete
        5. Old embeddings deleted after deprecation period
        """
        # Step 1: Register new model
        new_model = await db.fetch_one("""
            INSERT INTO embedding_model_registry
                (model_name, model_version, dimensions, status, activated_at)
            VALUES ($1, $2, $3, 'active', NOW())
            RETURNING id
        """, new_model_name, new_model_version, new_dimensions)
        
        # Step 2: Mark old model as deprecated
        old_model = await db.fetch_one("""
            UPDATE embedding_model_registry 
            SET status = 'deprecated', replaced_by = $1, deprecated_at = NOW()
            WHERE status = 'active' AND id != $1
            RETURNING id, model_name, model_version
        """, new_model['id'])
        
        # Step 3: Regenerate embeddings for existing content (background job)
        if old_model:
            await self._regenerate_all_embeddings(
                old_model_id=old_model['id'],
                new_model_id=new_model['id'],
                new_model_name=new_model_name,
                new_dimensions=new_dimensions
            )
    
    async def _regenerate_all_embeddings(
        self, old_model_id, new_model_id, new_model_name, new_dimensions
    ):
        """Regenerate embeddings for all content that used the old model."""
        for content_type in ['story', 'article', 'entity', 'claim', 'transcript_segment']:
            # Find all content with old model embeddings
            async for batch in fetch_batched(f"""
                SELECT em.content_id, em.content_version
                FROM embedding_metadata em
                WHERE em.content_type = $1
                  AND em.model_id = $2
                  AND em.is_current = true
            """, batch_size=100, content_type=content_type, model_id=old_model_id):
                
                for row in batch:
                    # Publish re-embedding event for each item
                    await redpanda.produce(
                        topic="embedding.generation.requested",
                        key=f"{content_type}:{row['content_id']}",
                        value={
                            "contentType": content_type,
                            "contentId": str(row['content_id']),
                            "modelName": new_model_name,
                            "reason": "model_upgrade",
                        }
                    )
    
    async def complete_migration(self, old_model_id: UUID):
        """Complete migration: delete old embeddings and archive old model."""
        # Verify all content has been re-embedded
        pending = await db.fetch_one("""
            SELECT COUNT(*) as count FROM embedding_metadata
            WHERE model_id = $1 AND is_current = true
        """, old_model_id)
        
        if pending['count'] > 0:
            raise MigrationIncompleteError(
                f"{pending['count']} embeddings still using old model"
            )
        
        # Delete old embeddings from Weaviate
        # (handled by the re-embedding process — old embeddings are overwritten)
        
        # Archive old model
        await db.execute("""
            UPDATE embedding_model_registry
            SET status = 'archived'
            WHERE id = $1
        """, old_model_id)
```

### Rule 5: Reindexing Strategy

Full reindexing is required when the embedding model changes or when recovering from data corruption. The reindex process regenerates all embeddings from PostgreSQL.

```python
async def reindex_all(tenant_id: Optional[str] = None):
    """Full reindex of Weaviate from PostgreSQL.
    
    Args:
        tenant_id: If provided, reindex only for this tenant.
    """
    logger.info(f"Starting full reindex for tenant: {tenant_id or 'ALL'}")
    start_time = time.monotonic()
    
    # Get active embedding model
    active_model = await db.fetch_one("""
        SELECT * FROM embedding_model_registry WHERE status = 'active'
    """)
    
    stats = {'total': 0, 'failed': 0}
    
    # Process each content type in order
    for content_type, table_query in [
        ("story", "SELECT s.id, sv.title, sv.summary, sv.content, ..."),
        ("article", "SELECT a.id, a.title, a.content, ..."),
        ("entity", "SELECT e.id, e.canonical_name, e.description, ..."),
        ("claim", "SELECT c.id, c.statement, ..."),
        ("transcript_segment", "SELECT t.id, t.text, t.segment_index, ..."),
    ]:
        async for batch in fetch_batched(table_query, batch_size=100, tenant_id=tenant_id):
            for row in batch:
                try:
                    # Generate embedding
                    provider = await AIProviderFactory.get_provider("embeddings")
                    text = self._prepare_text(content_type, row)
                    result = await provider.generate_embeddings(text)
                    
                    if result.success:
                        # Upsert to Weaviate
                        await self._upsert_to_weaviate(
                            class_name=self.CLASS_MAPPING[content_type],
                            uuid=row['id'],
                            vector=result.data['embedding'],
                            properties={...},
                            tenant=tenant_id or "global"
                        )
                        stats['total'] += 1
                    else:
                        stats['failed'] += 1
                        logger.error(f"Failed to embed {content_type} {row['id']}: {result.error}")
                
                except Exception as e:
                    stats['failed'] += 1
                    logger.error(f"Error embedding {content_type} {row['id']}: {e}")
    
    duration = time.monotonic() - start_time
    logger.info(f"Reindex complete: {stats['total']} embedded, "
                f"{stats['failed']} failed in {duration:.1f}s")
    return stats
```

**Reindex time estimates**:

| Content Type | Count | Time (text-embedding-3-small) | Time (text-embedding-3-large) |
|-------------|-------|------------------------------|------------------------------|
| Stories | 100,000 | ~30 min | ~60 min |
| Articles | 200,000 | ~60 min | ~120 min |
| Entities | 1,000,000 | ~5 hours | ~10 hours |
| Claims | 5,000,000 | ~25 hours | ~50 hours |
| Transcript Segments | 10,000,000 | ~50 hours | ~100 hours |
| **Total** | **~16.3M** | **~3.5 days** | **~7 days** |

**Mitigation for long reindex times**:
- Reindex by content type in priority order (stories first, then articles, then entities)
- Run reindex as a background process — new content continues to be indexed with the new model
- Old model embeddings remain available for query until migration is complete
- Use multiple parallel workers for different content types

### Rule 6: Tenant Isolation via Native Multi-Tenancy

Weaviate's native multi-tenancy provides tenant-level data isolation. Each tenant has its own isolated vector index within each class.

```python
class WeaviateTenantManager:
    """Manages Weaviate multi-tenancy."""
    
    async def ensure_tenant_exists(self, tenant_id: str):
        """Ensure a tenant exists in Weaviate for all classes."""
        for class_name in WEAVIATE_CLASSES:
            try:
                await self.client.schema.tenants.create(
                    class_name=class_name,
                    tenants=[tenant_id]
                )
            except Exception as e:
                if "already exists" not in str(e):
                    raise
    
    async def delete_tenant(self, tenant_id: str):
        """Delete a tenant and all its data from Weaviate."""
        for class_name in WEAVIATE_CLASSES:
            await self.client.schema.tenants.remove(
                class_name=class_name,
                tenants=[tenant_id]
            )

# Usage in search — automatically scoped to tenant
async def search_stories(query: str, tenant_id: str, limit: int = 20):
    """Search stories scoped to a specific tenant."""
    result = await weaviate_client.query.get(
        "Story", ["title", "summary", "content"]
    ).with_hybrid(
        query=query,
        alpha=0.75
    ).with_tenant(tenant_id).with_limit(limit).do()
    
    return result
```

**Global knowledge handling**: Global knowledge (tenant_id = NULL) is stored in a special "global" tenant. All authenticated users can query the global tenant in addition to their own tenant.

```python
async def search_all_accessible(query: str, tenant_id: str, limit: int = 20):
    """Search both tenant-specific and global knowledge."""
    # Search tenant-specific data
    tenant_results = await search_stories(query, tenant_id, limit)
    
    # Search global knowledge
    global_results = await search_stories(query, "global", limit)
    
    # Merge and rank results
    all_results = tenant_results + global_results
    all_results.sort(key=lambda x: x.get('_additional', {}).get('distance', 1.0))
    
    return all_results[:limit]
```

### Rule 7: Embedding Cost Tracking

Every embedding generation call records cost data, consistent with ADR-009's cost tracking decorator.

```python
async def _record_embedding_cost(
    self, 
    content_type: str, 
    content_id: UUID, 
    result: ProviderResult,
    text_length: int,
):
    """Record embedding generation cost."""
    usage = result.usage
    if not usage:
        return
    
    await db.execute("""
        INSERT INTO ai_cost_log
            (provider, model, prompt_version,
             input_tokens, output_tokens, total_tokens,
             input_cost_micro, output_cost_micro, total_cost_micro,
             execution_time_ms, provider_latency_ms,
             metadata, created_at)
        VALUES ($1, $2, 'embeddings',
                $3, 0, $3,
                $4, 0, $4,
                $5, $5,
                jsonb_build_object('content_type', $6, 'content_id', $7::text, 'text_length', $8),
                NOW())
    """, usage.provider, usage.model,
         usage.input_tokens,
         usage.input_cost_micro,
         usage.execution_time_ms,
         content_type, str(content_id), text_length)
```

### Rule 8: Human Review Gate

Only APPROVED or PUBLISHED content is embedded. The embedding service only subscribes to events that indicate approved content.

```python
# The embedding service only consumes these events:
# - StoryPublished (not StoryCreated)
# - ArticlePublished (not ArticleGenerated)
# - KnowledgeValidated (not KnowledgeExtracted)
# - ReviewApproved (not ReviewRequested)

async def handle_review_approved(self, event):
    """When review is approved, generate embedding for the content."""
    entity_type = event.data['entityType']
    entity_id = event.data['entityId']
    
    # Verify the entity is in APPROVED or PUBLISHED state
    entity = await self._fetch_entity(entity_type, entity_id)
    if entity['status'] not in ('APPROVED', 'PUBLISHED'):
        logger.warning(
            f"Review approved but entity {entity_id} has status {entity['status']}. "
            f"Skipping embedding."
        )
        return
    
    # Generate embedding
    await self._generate_embedding(entity_type, entity)
```

### Rule 9: Chunking Strategy for Long Content

Long content (transcripts, long articles) is chunked before embedding. Each chunk gets its own embedding and Weaviate object.

```python
class TextChunker:
    """Splits long text into chunks for embedding."""
    
    CHUNK_CONFIG = {
        "story": {"max_tokens": 8000, "overlap_tokens": 200},
        "article": {"max_tokens": 8000, "overlap_tokens": 200},
        "entity": {"max_tokens": 8000, "overlap_tokens": 0},  # Entities are short
        "claim": {"max_tokens": 8000, "overlap_tokens": 0},    # Claims are short
        "transcript_segment": {"max_tokens": 512, "overlap_tokens": 50},
    }
    
    def chunk_text(self, text: str, content_type: str) -> list[dict]:
        """Split text into chunks with overlap.
        
        Returns list of { "text": str, "chunk_index": int, "total_chunks": int }
        """
        config = self.CHUNK_CONFIG.get(content_type, self.CHUNK_CONFIG["story"])
        max_tokens = config["max_tokens"]
        overlap_tokens = config["overlap_tokens"]
        
        # Tokenize (approximate: 4 chars per token for Indonesian text)
        words = text.split()
        estimated_tokens = len(text) / 4
        
        if estimated_tokens <= max_tokens:
            return [{"text": text, "chunk_index": 0, "total_chunks": 1}]
        
        chunks = []
        # Simple chunking by word count (approximate)
        chunk_word_count = max_tokens * 4  # 4 chars per token
        overlap_word_count = overlap_tokens * 4
        
        start = 0
        chunk_index = 0
        while start < len(words):
            end = min(start + chunk_word_count, len(words))
            chunk_text = " ".join(words[start:end])
            chunks.append({
                "text": chunk_text,
                "chunk_index": chunk_index,
                "total_chunks": None,  # Set after all chunks are created
            })
            chunk_index += 1
            start = end - overlap_word_count if end < len(words) else end
        
        # Update total_chunks
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)
        
        return chunks
```

### Rule 10: Monitoring and Observability

Embedding service health and performance must be observable.

```python
# Prometheus metrics
embedding_generated = Counter(
    'embedding_generated_total',
    'Total embeddings generated',
    ['content_type', 'model', 'status']
)

embedding_latency = Histogram(
    'embedding_generation_duration_seconds',
    'Time to generate embedding',
    ['content_type', 'model']
)

embedding_queue_depth = Gauge(
    'embedding_queue_depth',
    'Number of items waiting for embedding',
    ['content_type']
)

weaviate_lag_seconds = Gauge(
    'weaviate_projection_lag_seconds',
    'Time since last Weaviate update',
    ['content_type']
)
```

**Grafana dashboard panels**:

| Panel | Query | Alert |
|-------|-------|-------|
| Embeddings Generated | `rate(embedding_generated_total[5m])` | — |
| Embedding Latency P95 | `histogram_quantile(0.95, embedding_generation_duration_seconds)` | > 5s → Warning |
| Embedding Failure Rate | `rate(embedding_generated_total{status="failed"}[5m])` | > 1% → Warning |
| Queue Depth | `embedding_queue_depth` | > 1000 → Warning |
| Weaviate Lag | `weaviate_projection_lag_seconds` | > 300s → Warning |
| Weaviate Object Count | Weaviate `Aggregate{Story{meta{count}}}` | — |
| Embedding Cost Rate | `rate(ai_cost_log_total_cost_micro[1h])` | > budget → Critical |

# Alternatives Considered

## Alternative 1: PostgreSQL pgvector Extension

**Description**: Use the `pgvector` PostgreSQL extension to store and query vector embeddings directly in PostgreSQL. No separate vector database is deployed.

**Advantages**:
- Zero additional infrastructure — PostgreSQL is already in the stack
- Strong consistency — no projection lag, no sync mechanism
- ACID transactions across relational data and vectors
- Simplified backup and recovery — one database to manage
- SQL-based queries with vector operations

**Disadvantages**:
- **No hybrid search**: pgvector supports vector search (IVFFlat, HNSW indexes) but does not natively support hybrid search (vector + BM25). Combining vector search with keyword search requires application-level merging of results.
- **No native multi-tenancy**: Tenant isolation must be implemented through application-level `WHERE tenant_id = ?` filters on vector queries. Weaviate provides native multi-tenancy.
- **Performance at scale**: pgvector's HNSW index performance degrades at 10M+ vectors compared to Weaviate's optimized HNSW implementation. Query latency increases significantly.
- **No built-in chunking or vectorizer management**: pgvector stores raw vectors but does not provide tools for managing embedding model versions, chunking strategies, or reindexing workflows.
- **No GraphQL API**: Weaviate provides a GraphQL API for complex queries (hybrid search, nearText, nearVector, filters). pgvector requires building query logic in application code.
- **No multi-modal support**: pgvector is text-only. Weaviate supports image, text, and cross-modal vectors for future multi-modal use cases.

**Rejection rationale**: pgvector is a viable option for simple vector search use cases, but the platform requires hybrid search (vector + BM25), native multi-tenancy, and a GraphQL query API. Weaviate provides these capabilities out of the box. The additional infrastructure cost of Weaviate is justified by the search quality and developer productivity benefits.

## Alternative 2: Elasticsearch with Dense Vector Plugin

**Description**: Use Elasticsearch with the dense vector plugin for vector search. Elasticsearch provides BM25 keyword search natively and vector search through the plugin. Hybrid search is supported through the `knn` query with `boost` parameters.

**Advantages**:
- Mature ecosystem with extensive documentation and community support
- Built-in BM25 keyword search (no separate system needed)
- Hybrid search with `knn` + `match` queries
- Scalable to billions of documents
- Rich query DSL for complex filtering and aggregation
- Already used by many organizations for search infrastructure

**Disadvantages**:
- **Operational complexity**: Elasticsearch requires significant operational expertise (cluster management, shard tuning, index optimization). For a small team, this is a heavy operational burden.
- **No native multi-tenancy**: Tenant isolation requires separate indices per tenant or application-level filtering. Weaviate's native multi-tenancy is simpler.
- **Dense vector plugin maturity**: The dense vector plugin is less mature than Weaviate's vector engine. Performance and feature parity are not guaranteed.
- **Higher resource consumption**: Elasticsearch clusters require more memory and CPU than Weaviate for equivalent vector search performance.
- **No GraphQL API**: Elasticsearch uses its own Query DSL. Weaviate's GraphQL API is more intuitive for complex search queries.
- **Index management overhead**: Elasticsearch requires explicit index management (mappings, settings, shards). Weaviate's schema is simpler to manage.
- **Embedding model management**: Elasticsearch does not provide tools for managing embedding model versions or reindexing workflows.

**Rejection rationale**: Elasticsearch is a powerful search engine but its operational complexity is not justified for the platform's vector search requirements. Weaviate provides equivalent or better vector search performance with significantly simpler operations. The team's small size (3–8 engineers) makes operational simplicity a priority.

## Alternative 3: Pinecone (Managed Vector Database)

**Description**: Use Pinecone as a managed vector database service. Pinecone handles infrastructure, scaling, and maintenance. The platform sends embeddings to Pinecone's API and queries via REST.

**Advantages**:
- Zero infrastructure management — Pinecone handles servers, scaling, and backups
- High-performance vector search with optimized HNSW indexes
- Built-in pod-based scaling for capacity management
- Simple REST API for indexing and querying
- Namespace-based isolation for multi-tenancy
- Serverless option for variable workloads

**Disadvantages**:
- **Vendor lock-in**: Pinecone is a proprietary service. Migrating away requires significant effort. Weaviate is open-source and can be self-hosted or used as a managed service.
- **No hybrid search**: Pinecone is vector-only. BM25 keyword search requires a separate system (e.g., Elasticsearch), adding infrastructure complexity.
- **No GraphQL API**: Pinecone provides a REST API. Complex queries require multiple API calls and application-level merging.
- **Egress costs**: Querying Pinecone from the platform's infrastructure incurs network egress costs. Self-hosted Weaviate has no egress costs.
- **No multi-modal support**: Pinecone is vector-only. Weaviate supports multi-modal vectors for future image/audio search.
- **Data sovereignty concerns**: Indonesian folklore data may have regulatory requirements for data residency. Self-hosted Weaviate provides full control over data location.
- **Cost at scale**: At 100M+ vectors, Pinecone's managed service costs can exceed self-hosted Weaviate by 3–5x.

**Rejection rationale**: Pinecone provides excellent managed vector search but lacks hybrid search, has vendor lock-in concerns, and may have data sovereignty issues for Indonesian cultural data. Weaviate's open-source model, hybrid search, and self-hosting capability make it a better fit for the platform's requirements and constraints.

## Alternative 4: Embeddings in PostgreSQL Only (No Vector Database)

**Description**: Store embeddings as JSONB arrays in PostgreSQL alongside the source data. Perform vector search by loading embeddings into application memory and computing cosine similarity in application code. No separate vector database.

**Advantages**:
- Simplest possible architecture — no additional infrastructure
- Strong consistency — embeddings are in the same database as source data
- No sync mechanism, no projection lag
- ACID transactions across content and embeddings
- Simplified backup and recovery

**Disadvantages**:
- **Brute-force search only**: Without a vector index (IVFFlat, HNSW), every search requires computing cosine similarity against ALL embeddings. At 100M embeddings, this is computationally infeasible.
- **No indexing**: PostgreSQL JSONB arrays cannot be indexed for vector search. Every query is a full table scan with distance computation.
- **Memory-bound**: Loading 100M embeddings into application memory requires ~600GB RAM (100M × 1536 dimensions × 4 bytes per float). This is not practical.
- **No hybrid search**: Combining vector search with keyword search requires application-level merging.
- **No tenant isolation at query time**: All embeddings are in the same table. Tenant filtering adds overhead to every query.
- **No GraphQL API**: All search logic must be built in application code.

**Rejection rationale**: Storing embeddings in PostgreSQL without a vector index is only feasible for very small datasets (< 10,000 vectors). At the platform's target scale of 100M embeddings, brute-force cosine similarity computation is computationally infeasible. A dedicated vector database with HNSW indexing is essential.

# Consequences

## Positive

1. **Semantic search across all content types**: Users can search stories, articles, entities, claims, and transcript segments using natural language queries. Results are ranked by semantic relevance, not just keyword matching.

2. **Hybrid search combines semantic and keyword**: Weaviate's hybrid search (alpha parameter) balances vector similarity with BM25 keyword matching. This provides better results than either approach alone — semantic understanding with keyword precision.

3. **Native multi-tenancy**: Weaviate's built-in multi-tenancy provides tenant-level data isolation without application-level filtering. Each tenant's vector index is physically isolated.

4. **Embedding model versioning**: The embedding model registry tracks which model produced each embedding. Model upgrades are managed through a controlled migration process with zero downtime.

5. **Full reindex capability**: The vector index can be fully rebuilt from PostgreSQL at any time. This eliminates the risk of Weaviate data corruption.

6. **Cost tracking per embedding**: Every embedding generation call records provider, model, token count, and cost. Cost analytics are available per content type and per model.

7. **Human review gate enforced by architecture**: The embedding service only consumes events for APPROVED/PUBLISHED content. REVIEW_REQUIRED content is never embedded.

8. **Chunking for long content**: Long transcripts and articles are chunked before embedding, with configurable chunk size and overlap. Each chunk gets its own embedding for granular search.

## Negative

1. **Embedding generation cost**: Every embedding requires an API call to an embedding provider. At 16.3M embeddings, the cost is significant (~$800–$2,000 for text-embedding-3-small, depending on text length).

2. **Reindex time at scale**: A full reindex at 16.3M embeddings takes ~3.5 days for text-embedding-3-small. During reindex, old embeddings remain available for query, but new embeddings are generated progressively.

3. **Storage overhead**: Weaviate stores vectors (1536 dimensions × 4 bytes = ~6KB per vector) plus inverted indexes and object properties. At 16.3M embeddings, estimated storage is ~100–200GB.

4. **Operational overhead of Weaviate**: Weaviate requires its own infrastructure (servers, storage, backup, monitoring). For a small team, this is an additional operational burden.

5. **Eventual consistency**: There is a delay between content publication and embedding availability in Weaviate. Newly published content is not immediately searchable.

6. **Chunking complexity**: Chunked content requires careful handling at query time. Search results may include multiple chunks from the same source document, requiring deduplication or aggregation.

7. **No cross-tenant search**: Native multi-tenancy prevents queries that span tenants. A researcher cannot search across all tenants' data. This is by design for security but limits cross-tenant discovery.

## Trade-offs

| Dimension | Benefit | Cost |
|-----------|---------|------|
| **Search quality** | Hybrid search (semantic + keyword) | Embedding generation cost (~$800–$2K for full reindex) |
| **Tenant isolation** | Native Weaviate multi-tenancy | No cross-tenant search |
| **Operational simplicity** | Weaviate is simpler than Elasticsearch | Additional infrastructure vs. pgvector-only approach |
| **Recoverability** | Full reindex from PostgreSQL | Reindex takes ~3.5 days at scale |
| **Query performance** | HNSW index for sub-100ms search | Storage overhead (~100–200GB at scale) |
| **Model flexibility** | Embedding model registry with migration | Migration requires full reindex |
| **Content granularity** | Chunking for long content | Chunk deduplication at query time |

# Risks

## Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Embedding provider API failure** | Low | Medium — new content not indexed | Queue embeddings for retry. Fallback to alternative embedding provider (ADR-009). |
| **Weaviate becomes unavailable** | Low | High — search queries fail | Circuit breaker in search services. Fall back to PostgreSQL full-text search (pg_trgm) as degraded mode. |
| **Embedding model deprecation** | Medium | Medium — new embeddings incompatible with old | Model registry manages migration. Old embeddings remain queryable during migration. |
| **HNSW index performance degradation** | Low | Medium — slow search queries | Monitor query latency. Tune efConstruction, ef, and maxConnections. Scale Weaviate nodes. |
| **Chunk boundary splits semantic meaning** | Medium | Low — reduced search quality for chunked content | Use overlapping chunks (200 token overlap). Ensure chunk boundaries align with paragraph breaks where possible. |
| **Weaviate disk space exhaustion** | Low | Critical — Weaviate crashes | Monitor disk usage. Set alerts at 70%, 85%, 95%. Implement data retention for archived content. |

## Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Reindex takes longer than expected** | Medium | Medium — extended migration window | Reindex by content type in priority order. Run as background process. Monitor progress. |
| **Embedding cost exceeds budget** | Medium | High — unexpected cloud costs | Set per-content-type cost budgets. Monitor embedding cost rate. Alert on cost anomalies. |
| **Weaviate backup strategy confusing** | Medium | Medium — incorrect recovery procedures | Document clear recovery runbooks. Weaviate recovery = reindex from PostgreSQL. |
| **Developer accidentally writes directly to Weaviate** | Medium | High — data inconsistency, broken provenance | Network-level isolation: Weaviate only accessible from embedding service subnets. Code review enforces no Weaviate clients in domain services. |
| **Hybrid search alpha tuning requires experimentation** | Medium | Low — suboptimal search results | Default alpha values per content type. A/B test alpha values in production. Monitor search click-through rates. |

## Future Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Multi-modal search (images, audio) required** | Text-only embeddings insufficient | Weaviate supports multi-modal vectors. Extend embedding service with image/audio embedding providers. |
| **Real-time search updates required** | Eventual consistency may not be sufficient | Reduce lag by moving from event-driven to CDC-based synchronization. |
| **Search quality requires fine-tuned embedding model** | General embedding models may not capture folklore-specific semantics | Fine-tune embedding model on Indonesian folklore corpus. Model registry supports custom models. |
| **Regulatory requirements for search explainability** | Must explain why a result was returned | Weaviate's `_additional { explainScore }` provides score explanation. Log search queries for audit. |
| **Vector dimension reduction required for scale** | 1536-dimension vectors at 100M+ scale may be expensive | Evaluate dimensionality reduction (PCA, Matryoshka embeddings). Weaviate supports variable-dimension vectors. |

# Future Revisions

This ADR may need revision under the following conditions:

1. **Multi-modal search required**: If the platform needs to search images (folklore illustrations, location photos) or audio (direct audio search, not via transcript), extend the embedding service with multi-modal embedding providers. Weaviate supports multi-modal vectors natively.

2. **Fine-tuned embedding model deployed**: If the platform fine-tunes an embedding model on Indonesian folklore data for improved search quality, the model registry must be extended to support custom models. The reindex process remains the same.

3. **Real-time search updates required**: If the platform needs sub-second embedding availability after content publication, replace event-driven embedding generation with CDC-based (Change Data Capture) synchronization using Debezium.

4. **Search quality requires re-ranking**: If initial search results need re-ranking by a more sophisticated model (e.g., cross-encoder), implement a two-stage search: Weaviate for candidate retrieval, re-ranking model for final ranking.

5. **Vector dimension reduction required**: If storage costs or query latency become prohibitive at scale, evaluate dimensionality reduction (PCA, Matryoshka embeddings) or switch to a lower-dimension embedding model.

6. **Weaviate cluster scaling required**: If query volume exceeds a single Weaviate node's capacity, implement Weaviate cluster with replication and sharding.

# References

- **Backend Platform PRD §3.4** — "PostgreSQL as Source of Truth" — Weaviate is a projection, not a source of truth.
- **Backend Platform PRD §11** — "Database Strategy" — Weaviate stores embeddings, chunks, search metadata. Read only.
- **AI Platform PRD §6.7** — "Embedding Service" — Generates vectors for stories, articles, entities, knowledge, claims.
- **AI Platform PRD §12** — "Queue Architecture" — `embedding.generation.requested` and `embedding.generated` topics.
- **ADR-001: PostgreSQL as Source of Truth** — Weaviate as read-only vector projection.
- **ADR-003: Event-Driven Architecture** — Event replay for reindexing.
- **ADR-004: Queue-Driven AI Platform** — Embedding service consumes events, writes to Weaviate.
- **ADR-005: Multi-Tenant Architecture** — Weaviate native multi-tenancy for tenant isolation.
- **ADR-007: Canonical Story Core Contract** — Story content embedded for semantic search.
- **ADR-008: Immutable Versioning** — Embeddings tied to content version; re-embedded on version change.
- **ADR-009: AI Provider Abstraction** — Embedding provider abstraction (OpenAI primary, Gemini fallback).
- **Weaviate Documentation** — https://weaviate.io/developers/weaviate — Architecture, schema, hybrid search, multi-tenancy.
- **Weaviate Hybrid Search** — https://weaviate.io/developers/weaviate/search/hybrid — Alpha parameter, BM25 + vector fusion.
- **Weaviate Multi-Tenancy** — https://weaviate.io/developers/weaviate/manage-data/multi-tenancy — Native tenant isolation.
- **OpenAI Embeddings** — https://platform.openai.com/docs/guides/embeddings — text-embedding-3-small and text-embedding-3-large.
- **HNSW Algorithm** — https://arxiv.org/abs/1603.09320 — Approximate Nearest Neighbor search for vector indexing.