package id.livingatlas.sharedevents;

/**
 * Central registry of Redpanda topics for service-to-service and 
 * services-to-ai-platform communication.
 * 
 * This is the SINGLE SOURCE OF TRUTH for all topic names.
 * 
 * Convention: {domain}.{action}[.{qualifier}]
 * - Domain: source, transcript, story, knowledge, article, embedding, graph, review, publication
 * - Action: submitted, imported, extracted, normalized, validated, generated, projected, etc.
 * - Qualifier: requested (command events), dlq (dead letter queues)
 * 
 * Reference: docs/ai-platform/queue-contract-specification.md
 * Reference: docs/ai-platform/domain-event-catalog.md
 */
public final class EventTopics {

    private EventTopics() {}

    // =================================================================
    // Source Topics
    // =================================================================
    
    /** 
     * New source material submitted for AI pipeline processing.
     * Producer: content-service (Spring Boot)
     * Consumer: orchestration-service (Python)
     */
    public static final String SOURCE_SUBMITTED = "source.submitted";

    /**
     * External metadata has been extracted and normalized.
     * Producer: ingestion-service (Python)
     * Consumer: content-service (Spring Boot), orchestration-service (Python)
     */
    public static final String SOURCE_METADATA_IMPORTED = "source.metadata.imported";

    // =================================================================
    // Transcript Topics
    // =================================================================

    /**
     * Raw transcript text has been imported.
     * Producer: ingestion-service (Python)
     * Consumer: orchestration-service (Python), content-service (Spring Boot)
     */
    public static final String TRANSCRIPT_IMPORTED = "transcript.imported";

    /**
     * Transcript has been cleaned, segmented, and normalized.
     * Producer: ingestion-service (Python)
     * Consumer: orchestration-service (Python)
     */
    public static final String TRANSCRIPT_NORMALIZED = "transcript.normalized";

    // =================================================================
    // Story Topics
    // =================================================================

    /**
     * Request to extract a canonical story from transcript.
     * Producer: orchestration-service (Python)
     * Consumer: extraction-service (Python)
     */
    public static final String STORY_EXTRACTION_REQUESTED = "story.extraction.requested";

    /**
     * Canonical story has been successfully extracted.
     * Producer: extraction-service (Python)
     * Consumer: orchestration-service (Python), content-service (Spring Boot)
     */
    public static final String STORY_EXTRACTED = "story.extracted";

    /**
     * Story has been published and is live.
     * Producer: content-service (Spring Boot)
     * Consumer: knowledge-service (Spring Boot), research-service (Spring Boot)
     */
    public static final String STORY_PUBLISHED = "story.published";

    // =================================================================
    // Knowledge Topics
    // =================================================================

    /**
     * Request to extract structured knowledge from story.
     * Producer: orchestration-service (Python)
     * Consumer: extraction-service (Python)
     */
    public static final String KNOWLEDGE_EXTRACTION_REQUESTED = "knowledge.extraction.requested";

    /**
     * Knowledge entities, claims, themes, motifs extracted.
     * Producer: extraction-service (Python)
     * Consumer: orchestration-service (Python), knowledge-service (Spring Boot)
     */
    public static final String KNOWLEDGE_EXTRACTED = "knowledge.extracted";

    /**
     * Request to normalize and resolve ambiguities.
     * Producer: orchestration-service (Python)
     * Consumer: normalization-service (Python)
     */
    public static final String KNOWLEDGE_NORMALIZATION_REQUESTED = "knowledge.normalization.requested";

    /**
     * Knowledge normalized; aliases resolved, duplicates merged.
     * Producer: normalization-service (Python)
     * Consumer: orchestration-service (Python), knowledge-service (Spring Boot)
     */
    public static final String KNOWLEDGE_NORMALIZED = "knowledge.normalized";

    /**
     * Request to validate knowledge quality.
     * Producer: orchestration-service (Python)
     * Consumer: validation-service (Python)
     */
    public static final String KNOWLEDGE_VALIDATION_REQUESTED = "knowledge.validation.requested";

    /**
     * Knowledge has passed or failed validation.
     * Producer: validation-service (Python)
     * Consumer: orchestration-service (Python), knowledge-service (Spring Boot)
     */
    public static final String KNOWLEDGE_VALIDATED = "knowledge.validated";

    // =================================================================
    // Article Topics
    // =================================================================

    /**
     * Request to generate an article from validated knowledge.
     * Producer: orchestration-service (Python)
     * Consumer: article-service (Python)
     */
    public static final String ARTICLE_GENERATION_REQUESTED = "article.generation.requested";

    /**
     * Article draft has been generated.
     * Producer: article-service (Python)
     * Consumer: orchestration-service (Python), workflow-service (Spring Boot)
     */
    public static final String ARTICLE_GENERATED = "article.generated";

    // =================================================================
    // Embedding Topics
    // =================================================================

    /**
     * Request to generate embeddings for knowledge artifacts.
     * Producer: orchestration-service (Python)
     * Consumer: embedding-service (Python)
     */
    public static final String EMBEDDING_GENERATION_REQUESTED = "embedding.generation.requested";

    /**
     * Embeddings have been generated and stored.
     * Producer: embedding-service (Python)
     * Consumer: orchestration-service (Python), weaviate-sync (Python)
     */
    public static final String EMBEDDING_GENERATED = "embedding.generated";

    // =================================================================
    // Graph Projection Topics
    // =================================================================

    /**
     * Request to update the knowledge graph projection.
     * Producer: orchestration-service (Python)
     * Consumer: neo4j-sync (Python)
     */
    public static final String GRAPH_PROJECTION_REQUESTED = "graph.projection.requested";

    /**
     * Knowledge graph projection has been updated.
     * Producer: neo4j-sync (Python)
     * Consumer: orchestration-service (Python)
     */
    public static final String GRAPH_PROJECTED = "graph.projected";

    // =================================================================
    // Workflow / Review Topics
    // =================================================================

    /**
     * Content submitted for human review.
     * Producer: orchestration-service (Python) / content-service (Spring Boot)
     * Consumer: workflow-service (Spring Boot)
     */
    public static final String REVIEW_REQUESTED = "review.requested";

    /**
     * Content approved by reviewer.
     * Producer: workflow-service (Spring Boot)
     * Consumer: orchestration-service (Python), content-service (Spring Boot), knowledge-service (Spring Boot)
     */
    public static final String REVIEW_APPROVED = "review.approved";

    /**
     * Content rejected by reviewer.
     * Producer: workflow-service (Spring Boot)
     * Consumer: orchestration-service (Python), content-service (Spring Boot), knowledge-service (Spring Boot)
     */
    public static final String REVIEW_REJECTED = "review.rejected";

    // =================================================================
    // Publication Topics
    // =================================================================

    /**
     * Request to publish approved content.
     * Producer: workflow-service (Spring Boot)
     * Consumer: content-service (Spring Boot)
     */
    public static final String PUBLICATION_REQUESTED = "publication.requested";

    /**
     * Content has been published and is live.
     * Producer: content-service (Spring Boot)
     * Consumer: orchestration-service (Python), knowledge-service (Spring Boot), research-service (Spring Boot)
     */
    public static final String PUBLICATION_COMPLETED = "publication.completed";

    /**
     * Article has been published after human review.
     * Producer: content-service (Spring Boot)
     * Consumer: article-service (Python, for feedback loop)
     */
    public static final String ARTICLE_PUBLISHED = "article.published";

    // =================================================================
    // Legacy / Migration Support
    // =================================================================
    // These topics are maintained for backward compatibility.
    // New code should use the standard topics above.

    /** @deprecated Use {@link #SOURCE_SUBMITTED} instead. */
    @Deprecated
    public static final String SOURCE_REGISTERED = SOURCE_SUBMITTED;

    /** @deprecated Use {@link #STORY_EXTRACTED} instead. */
    @Deprecated
    public static final String STORY_CREATED = "ai.story.created";

    /** @deprecated Use {@link #ARTICLE_GENERATED} instead. */
    @Deprecated
    public static final String ARTICLE_DRAFT_CREATED = "ai.article.draft.created";

    /** @deprecated Use {@link #REVIEW_APPROVED} or {@link #REVIEW_REJECTED} instead. */
    @Deprecated
    public static final String REVIEW_COMPLETED = "workflow.review.completed";
}