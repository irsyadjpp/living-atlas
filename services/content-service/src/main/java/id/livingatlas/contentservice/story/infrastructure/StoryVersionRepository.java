package id.livingatlas.contentservice.story.infrastructure;

import id.livingatlas.contentservice.story.domain.StoryVersion;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface StoryVersionRepository extends JpaRepository<StoryVersion, UUID> {
    List<StoryVersion> findByStoryIdOrderByVersionNumberDesc(UUID storyId);
}