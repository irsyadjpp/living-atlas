package id.livingatlas.researchservice.adaptation.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "adaptation_scores", schema = "research")
@Getter
@Setter
@NoArgsConstructor
public class AdaptationScore {

    @Id
    @Column(name = "story_id")
    private UUID storyId;

    @Column(name = "movie_score", precision = 5, scale = 2)
    private BigDecimal movieScore;

    @Column(name = "series_score", precision = 5, scale = 2)
    private BigDecimal seriesScore;

    @Column(name = "documentary_score", precision = 5, scale = 2)
    private BigDecimal documentaryScore;

    @Column(name = "podcast_score", precision = 5, scale = 2)
    private BigDecimal podcastScore;

    @Column(name = "novel_score", precision = 5, scale = 2)
    private BigDecimal novelScore;

    @Column(name = "game_score", precision = 5, scale = 2)
    private BigDecimal gameScore;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;
}