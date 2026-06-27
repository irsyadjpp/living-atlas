package id.livingatlas.contentservice.story.application;
import id.livingatlas.contentservice.story.domain.StoryStatus;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.contentservice.story.domain.Story;
import id.livingatlas.contentservice.story.domain.StoryEvidence;
import id.livingatlas.contentservice.story.domain.StoryVersion;
import id.livingatlas.contentservice.story.infrastructure.StoryEvidenceRepository;
import id.livingatlas.contentservice.story.infrastructure.StoryRepository;
import id.livingatlas.contentservice.story.infrastructure.StoryVersionRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class StoryService {

    private final StoryRepository storyRepository;
    private final StoryVersionRepository storyVersionRepository;
    private final StoryEvidenceRepository storyEvidenceRepository;

    @Transactional
    public Story createStory(Story story) {
        story.setStatus(StoryStatus.DRAFT);
        Story saved = storyRepository.save(story);
        log.info("Story created: id={}, title={}", saved.getId(), saved.getTitle());
        return saved;
    }

    @Transactional(readOnly = true)
    public Story getStory(UUID id) {
        return storyRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Story not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Story> listStories(int page, int size, String type, String status) {
        return storyRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Story updateStory(UUID id, Story updates) {
        Story story = getStory(id);
        if (updates.getTitle() != null) story.setTitle(updates.getTitle());
        if (updates.getSummary() != null) story.setSummary(updates.getSummary());
        return storyRepository.save(story);
    }

    @Transactional
    public StoryVersion createVersion(UUID storyId, StoryVersion version) {
        Story story = getStory(storyId);
        version.setStoryId(storyId);
        StoryVersion saved = storyVersionRepository.save(version);
        log.info("Story version created: storyId={}, version={}", storyId, version.getVersionNumber());
        return saved;
    }

    @Transactional(readOnly = true)
    public List<StoryVersion> getVersions(UUID storyId) {
        return storyVersionRepository.findByStoryIdOrderByVersionNumberDesc(storyId);
    }

    @Transactional
    public void deleteStory(UUID id) {
        storyRepository.deleteById(id);
        log.info("Story soft-deleted: id={}", id);
    }

    @Transactional(readOnly = true)
    public List<StoryEvidence> getEvidence(UUID storyId) {
        return storyEvidenceRepository.findByStoryId(storyId);
    }

    @Transactional
    public StoryEvidence addEvidence(StoryEvidence evidence) {
        return storyEvidenceRepository.save(evidence);
    }
}