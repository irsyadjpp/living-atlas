package id.livingatlas.researchservice.genome.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "story_genomes", schema = "research")
@Getter
@Setter
@NoArgsConstructor
public class StoryGenome {

    @Id
    @Column(name = "story_id")
    private UUID storyId;

    @Column(name = "dna_version", nullable = false)
    private Integer dnaVersion = 1;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "theme_vector", columnDefinition = "jsonb")
    private Map<String, Object> themeVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "motif_vector", columnDefinition = "jsonb")
    private Map<String, Object> motifVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "archetype_vector", columnDefinition = "jsonb")
    private Map<String, Object> archetypeVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "narrative_pattern_vector", columnDefinition = "jsonb")
    private Map<String, Object> narrativePatternVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "culture_vector", columnDefinition = "jsonb")
    private Map<String, Object> cultureVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "emotional_vector", columnDefinition = "jsonb")
    private Map<String, Object> emotionalVector;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}