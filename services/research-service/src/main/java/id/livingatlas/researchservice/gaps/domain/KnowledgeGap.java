package id.livingatlas.researchservice.gaps.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Table(name = "knowledge_gaps", schema = "research")
@Getter
@Setter
@NoArgsConstructor
public class KnowledgeGap {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "gap_type", length = 100)
    private String gapType;

    @Column(name = "entity_id")
    private UUID entityId;

    @Column(columnDefinition = "text")
    private String description;

    @Column(name = "priority_score", precision = 5, scale = 2)
    private BigDecimal priorityScore;

    @Column(length = 50)
    private String status;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "created_by")
    private UUID createdBy;
}