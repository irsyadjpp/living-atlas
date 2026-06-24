package id.livingatlas.contentservice.story.infrastructure;

import id.livingatlas.contentservice.story.domain.StoryEvidence;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface StoryEvidenceRepository extends JpaRepository<StoryEvidence, UUID> {
    List<StoryEvidence> findByStoryId(UUID storyId);
}