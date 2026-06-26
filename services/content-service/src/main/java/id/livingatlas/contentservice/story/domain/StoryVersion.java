package id.livingatlas.contentservice.story.domain;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.Map;
import java.util.UUID;

/**
 * Immutable version record for a Story.
 * <p>
 * Each version is created via INSERT only — never updated.
 * The version chain is maintained through {@code previousVersionId}.
 * The aggregate root ({@link Story}) points to the current version
 * via {@code currentVersionId}.
 * <p>
 * Per ADR-008: Immutable Versioning — Append-Only, No Overwrite.
 *
 * @see Story
 */
@Entity
@Table(name = "story_versions", schema = "content",
       uniqueConstraints = @UniqueConstraint(columnNames = {"story_id", "version_number"}))
@Getter
@Setter
@NoArgsConstructor
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class StoryVersion {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @EqualsAndHashCode.Include
    private UUID id;

    @Column(name = "story_id", nullable = false)
    private UUID storyId;

    @Column(name = "version_number", nullable = false)
    private int versionNumber;

    @Column(nullable = false, columnDefinition = "text")
    private String title;

    @Column(columnDefinition = "text")
    private String summary;

    @Enumerated(EnumType.STRING)
    @JdbcTypeCode(SqlTypes.NAMED_ENUM)
    @Column(name = "story_type", nullable = false, columnDefinition = "content.story_type")
    private StoryType storyType;

    @Enumerated(EnumType.STRING)
    @Column(name = "narrative_type", length = 50)
    private StoryNarrativeType narrativeType;

    @Column(name = "language_code", length = 20)
    private String languageCode;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> content;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(columnDefinition = "jsonb")
    private Map<String, Object> metadata;

    @Column(name = "previous_version_id")
    private UUID previousVersionId;

    @Column(name = "change_reason", columnDefinition = "text")
    private String changeReason;

    @Column(name = "change_type", nullable = false, length = 50)
    private String changeType;

    @Column(name = "created_by", nullable = false)
    private UUID createdBy;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}