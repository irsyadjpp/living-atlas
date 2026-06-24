package id.livingatlas.researchservice.genome.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "story_similarity", schema = "research")
@Getter
@Setter
@NoArgsConstructor
@IdClass(StorySimilarityId.class)
public class StorySimilarity {

    @Id
    @Column(name = "story_id_a", nullable = false)
    private UUID storyIdA;

    @Id
    @Column(name = "story_id_b", nullable = false)
    private UUID storyIdB;

    @Column(name = "similarity_score", precision = 8, scale = 6)
    private BigDecimal similarityScore;

    @Column(name = "similarity_method", length = 100)
    private String similarityMethod;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;
}