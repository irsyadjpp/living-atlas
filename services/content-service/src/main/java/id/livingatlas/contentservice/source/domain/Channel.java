package id.livingatlas.contentservice.source.domain;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.hibernate.annotations.UpdateTimestamp;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

@Entity
@Table(name = "channels", schema = "source")
@Data
@NoArgsConstructor
@SQLRestriction("is_deleted = false")
@SQLDelete(sql = "UPDATE source.channels SET is_deleted = true, deleted_at = now(), deleted_by = ? WHERE id = ?")
public class Channel {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false, length = 50)
    private String platform;

    @Column(name = "platform_channel_id", nullable = false, length = 255)
    private String platformChannelId;

    @Column(length = 255)
    private String slug;

    @Column(nullable = false, length = 500)
    private String name;

    @Column(columnDefinition = "text")
    private String description;

    @Column(name = "country_code", length = 10)
    private String countryCode;

    @Column(name = "language_code", length = 20)
    private String languageCode;

    @Column(name = "channel_url", columnDefinition = "text")
    private String channelUrl;

    @Column(name = "avatar_url", columnDefinition = "text")
    private String avatarUrl;

    @Column(name = "banner_url", columnDefinition = "text")
    private String bannerUrl;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb", nullable = false)
    private Map<String, Object> metadata;

    @Column(name = "tenant_id")
    private UUID tenantId;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "created_by")
    private UUID createdBy;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
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

    public Channel(String platform, String platformChannelId, String name) {
        this.platform = platform;
        this.platformChannelId = platformChannelId;
        this.name = name;
        this.metadata = Map.of();
        this.version = 1L;
        this.isDeleted = false;
    }
}