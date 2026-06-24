package id.livingatlas.knowledgeservice.knowledge.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.hibernate.type.SqlTypes;

import java.math.BigDecimal;
import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "objects", schema = "knowledge")
@Getter
@Setter
@NoArgsConstructor
@SQLRestriction("is_deleted = false")
@SQLDelete(sql = "UPDATE knowledge.objects SET is_deleted = true, deleted_at = now(), deleted_by = ? WHERE id = ?")
public class KnowledgeObject {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "object_type", nullable = false, length = 100)
    private String objectType;

    @Column(name = "canonical_name", nullable = false, columnDefinition = "text")
    private String canonicalName;

    @Column(unique = true, length = 500)
    private String slug;

    @Column(columnDefinition = "text")
    private String summary;

    @Column(name = "confidence_score", precision = 5, scale = 2)
    private BigDecimal confidenceScore;

    @Column(length = 50)
    private String status;

    @Column(name = "tenant_id")
    private UUID tenantId;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb", nullable = false)
    private Map<String, Object> metadata;

    @Column(name = "created_at")
    private OffsetDateTime createdAt;

    @Column(name = "created_by")
    private UUID createdBy;

    @Column(name = "updated_at")
    private OffsetDateTime updatedAt;

    @Column(name = "updated_by")
    private UUID updatedBy;

    @Column(name = "deleted_at")
    private OffsetDateTime deletedAt;

    @Column(name = "deleted_by")
    private UUID deletedBy;

    @Version
    @Column(nullable = false)
    private Long version = 1L;

    @Column(name = "is_deleted", nullable = false)
    private Boolean isDeleted = false;
}