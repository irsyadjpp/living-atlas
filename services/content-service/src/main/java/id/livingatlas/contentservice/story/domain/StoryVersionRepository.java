package id.livingatlas.contentservice.story.domain;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository for {@link StoryVersion} entities.
 */
@Repository
public interface StoryVersionRepository extends JpaRepository<StoryVersion, UUID> {

    List<StoryVersion> findByStoryIdOrderByVersionNumberDesc(UUID storyId);

    Optional<StoryVersion> findByStoryIdAndVersionNumber(UUID storyId, int versionNumber);

    int countByStoryId(UUID storyId);
}