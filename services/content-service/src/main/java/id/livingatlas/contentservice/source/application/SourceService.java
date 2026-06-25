package id.livingatlas.contentservice.source.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.contentservice.infrastructure.AiEventPublisher;
import id.livingatlas.contentservice.source.domain.Channel;
import id.livingatlas.contentservice.source.domain.Source;
import id.livingatlas.contentservice.source.infrastructure.ChannelRepository;
import id.livingatlas.contentservice.source.infrastructure.SourceRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class SourceService {

    private final SourceRepository sourceRepository;
    private final ChannelRepository channelRepository;
    private final AiEventPublisher eventPublisher;

    @Transactional
    public Channel registerChannel(Channel channel) {
        Channel saved = channelRepository.save(channel);
        log.info("Channel registered: id={}, name={}, platform={}", saved.getId(), saved.getName(), saved.getPlatform());
        return saved;
    }

    /**
     * Register a YouTube source and publish event to trigger AI pipeline ingestion.
     * This is the entry point for the event-driven AI pipeline.
     */
    @Transactional
    public Source registerSourceAndPublish(Source source) {
        source.setStatus("submitted");
        Source saved = sourceRepository.save(source);
        log.info("Source registered with AI trigger: id={}, videoId={}", saved.getId(), saved.getPlatformVideoId());
        
        eventPublisher.publishSourceSubmitted(
            "youtube_video",
            saved.getPlatformVideoId(),
            saved.getChannelId()
        );
        
        return saved;
    }

    /**
     * Register a YouTube channel and publish event to trigger AI pipeline crawling.
     */
    @Transactional
    public Channel registerChannelAndPublish(Channel channel) {
        Channel saved = channelRepository.save(channel);
        log.info("Channel registered with AI trigger: id={}, handle={}", saved.getId(), saved.getPlatformChannelId());
        
        eventPublisher.publishSourceSubmitted(
            "youtube_channel",
            saved.getPlatformChannelId(),
            saved.getId()
        );
        
        return saved;
    }

    @Transactional(readOnly = true)
    public Channel getChannel(UUID id) {
        return channelRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Channel not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Channel> listChannels(int page, int size) {
        return channelRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Source registerSource(Source source) {
        source.setStatus("registered");
        Source saved = sourceRepository.save(source);
        log.info("Source registered: id={}, title={}", saved.getId(), saved.getTitle());
        return saved;
    }

    @Transactional(readOnly = true)
    public Source getSource(UUID id) {
        return sourceRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Source not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Source> listSources(int page, int size, UUID channelId) {
        if (channelId != null) {
            return sourceRepository.findByChannelId(channelId, PageRequest.of(page, size));
        }
        return sourceRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public void deleteSource(UUID id) {
        sourceRepository.deleteById(id);
        log.info("Source soft-deleted: id={}", id);
    }

    /**
     * Publish a source.submitted event without saving to DB.
     * Used by the event-driven YouTube endpoints (content-service → Queue → AI Worker).
     */
    public void publishSourceSubmittedEvent(String sourceType, String platformSourceId, UUID channelId) {
        eventPublisher.publishSourceSubmitted(sourceType, platformSourceId, channelId);
        log.info("Source event published (no DB save): type={}, sourceId={}", sourceType, platformSourceId);
    }
}
