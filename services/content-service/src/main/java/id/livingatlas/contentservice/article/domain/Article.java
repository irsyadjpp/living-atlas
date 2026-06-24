package id.livingatlas.contentservice.article.domain;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "articles", schema = "content")
@Getter
@Setter
@NoArgsConstructor
@SQLRestriction("is_deleted = false")
@SQLDelete(sql = "UPDATE content.articles SET is_deleted = true, deleted_at = now(), deleted_by = ? WHERE id = ?")
public class Article {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "story_id")
    private UUID storyId;

    @Enumerated(EnumType.STRING)
    @Column(name = "article_type", nullable = false)
    private ArticleType articleType;

    @Column(nullable = false, columnDefinition = "text")
    private String title;

    @Column(columnDefinition = "text")
    private String content;

    @Column(length = 50)
    private String status;

    @Column(name = "tenant_id")
    private UUID tenantId;

    @Column(name = "workspace_id")
    private UUID workspaceId;

    @Column(name = "owner_id")
    private UUID ownerId;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
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