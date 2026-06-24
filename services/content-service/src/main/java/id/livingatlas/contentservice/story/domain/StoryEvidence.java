package id.livingatlas.contentservice.story.domain;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "story_evidence", schema = "content")
@Data
@NoArgsConstructor
public class StoryEvidence {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "story_id", nullable = false)
    private UUID storyId;

    @Column(name = "transcript_segment_id")
    private UUID transcriptSegmentId;

    @Enumerated(EnumType.STRING)
    @Column(name = "evidence_level", nullable = false)
    private EvidenceLevel evidenceLevel;

    @Column(name = "confidence_score", precision = 5, scale = 2)
    private BigDecimal confidenceScore;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;
}