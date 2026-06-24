package id.livingatlas.contentservice.source.api;

import id.livingatlas.contentservice.source.api.dto.CrawlChannelRequest;
import id.livingatlas.contentservice.source.api.dto.CrawlVideoRequest;
import id.livingatlas.contentservice.source.application.SourceService;
import id.livingatlas.contentservice.source.domain.Channel;
import id.livingatlas.contentservice.source.domain.Source;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.net.URL;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/sources")
@RequiredArgsConstructor
public class SourceController {

    private final SourceService sourceService;

    // =================================================================
    // YouTube AI Pipeline Endpoints (Event-Driven)
    // These endpoints register the source and trigger the AI pipeline
    // via Redpanda events. The actual crawling is done by ai-platform.
    // =================================================================

    /**
     * Submit a YouTube video for AI pipeline processing.
     * This saves the source to PostgreSQL and publishes a source.submitted event
     * to Redpanda. The ai-platform/orchestration-service consumes the event and
     * triggers the actual YouTube crawling via ingestion-service.
     *
     * Request body examples:
     *   {"platformVideoId": "dQw4w9WgXcQ"}
     *   {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
     */
    @PostMapping("/youtube/videos")
    public ResponseEntity<Map<String, Object>> crawlYoutubeVideo(
            @Valid @RequestBody CrawlVideoRequest request) {
        // Resolve platform video ID from URL if needed
        String platformVideoId = request.getPlatformVideoId();
        if (platformVideoId == null && request.getUrl() != null) {
            platformVideoId = resolveYoutubeVideoId(request.getUrl());
        }

        // Publish event to trigger AI pipeline — ingestion service will create the video record
        // after successful YouTube crawl. This follows the event-driven architecture:
        // Backend → Queue → AI Worker (NOT Backend → DB + Queue)
        java.util.UUID tempId = java.util.UUID.randomUUID();
        sourceService.publishSourceSubmittedEvent("youtube_video", platformVideoId, null);

        return ResponseEntity.status(HttpStatus.ACCEPTED).body(Map.of(
            "id", tempId,
            "platformVideoId", platformVideoId,
            "status", "submitted",
            "message", "Source submitted for AI pipeline processing"
        ));
    }

    /**
     * Submit a YouTube channel for AI pipeline crawling.
     * The AI platform will discover and crawl all videos from this channel.
     *
     * Request body examples:
     *   {"handle": "@RJL5-FAJARADITYA", "maxVideos": 10}
     *   {"handle": "RJL5-FAJARADITYA"}
     *   {"handle": "https://www.youtube.com/@RJL5-FAJARADITYA"}
     */
    @PostMapping("/youtube/channels")
    public ResponseEntity<Map<String, Object>> crawlYoutubeChannel(
            @Valid @RequestBody CrawlChannelRequest request) {
        String channelUrl = resolveChannelUrl(request.getHandle());
        String platformChannelId = extractChannelIdFromUrl(channelUrl);

        // Create channel record
        Channel channel = new Channel("youtube", platformChannelId, request.getHandle());
        channel.setChannelUrl(channelUrl);
        channel.setMetadata(Map.of(
            "maxVideos", request.getMaxVideos() != null ? request.getMaxVideos() : 50,
            "handle", request.getHandle()
        ));

        Channel saved = sourceService.registerChannelAndPublish(channel);

        return ResponseEntity.status(HttpStatus.ACCEPTED).body(Map.of(
            "id", saved.getId(),
            "channelHandle", request.getHandle(),
            "maxVideos", request.getMaxVideos(),
            "status", "submitted",
            "message", "Channel submitted for AI pipeline crawling"
        ));
    }

    // =================================================================
    // Direct Source/Channel CRUD (no AI pipeline trigger)
    // =================================================================

    @PostMapping("/channels")
    public ResponseEntity<Channel> registerChannel(@RequestBody Channel channel) {
        return ResponseEntity.status(HttpStatus.CREATED).body(sourceService.registerChannel(channel));
    }

    @GetMapping("/channels/{id}")
    public ResponseEntity<Channel> getChannel(@PathVariable UUID id) {
        return ResponseEntity.ok(sourceService.getChannel(id));
    }

    @GetMapping("/channels")
    public ResponseEntity<Page<Channel>> listChannels(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size) {
        return ResponseEntity.ok(sourceService.listChannels(page, size));
    }

    @PostMapping("/videos")
    public ResponseEntity<Source> registerSource(@RequestBody Source source) {
        return ResponseEntity.status(HttpStatus.CREATED).body(sourceService.registerSource(source));
    }

    @GetMapping("/videos/{id}")
    public ResponseEntity<Source> getSource(@PathVariable UUID id) {
        return ResponseEntity.ok(sourceService.getSource(id));
    }

    @GetMapping("/videos")
    public ResponseEntity<Page<Source>> listSources(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) UUID channelId) {
        return ResponseEntity.ok(sourceService.listSources(page, size, channelId));
    }

    @DeleteMapping("/videos/{id}")
    public ResponseEntity<Void> deleteSource(@PathVariable UUID id) {
        sourceService.deleteSource(id);
        return ResponseEntity.noContent().build();
    }

    // =================================================================
    // URL Helpers
    // =================================================================

    /**
     * Extract YouTube video ID from various URL formats.
     * Supports: youtube.com/watch?v=VIDEO_ID, youtu.be/VIDEO_ID, etc.
     */
    private String resolveYoutubeVideoId(String url) {
        if (url == null) return null;
        try {
            var parsed = new URL(url);
            String path = parsed.getPath();
            String query = parsed.getQuery();

            // youtube.com/watch?v=VIDEO_ID
            if (query != null && query.contains("v=")) {
                String[] params = query.split("&");
                for (String param : params) {
                    if (param.startsWith("v=")) {
                        return param.substring(2);
                    }
                }
            }
            // youtu.be/VIDEO_ID
            if (path != null && path.length() > 1 && parsed.getHost().contains("youtu.be")) {
                return path.substring(1);
            }
        } catch (Exception e) {
            // If not a URL, assume it's already a video ID
        }
        return url; // Return as-is if not parseable
    }

    /**
     * Convert a YouTube handle or ID to a full channel URL.
     */
    private String resolveChannelUrl(String handle) {
        if (handle == null) return null;
        handle = handle.trim();
        if (handle.startsWith("http://") || handle.startsWith("https://")) {
            return handle;
        }
        if (handle.startsWith("@")) {
            return "https://www.youtube.com/" + handle;
        }
        if (handle.startsWith("UC") && handle.length() == 24) {
            return "https://www.youtube.com/channel/" + handle;
        }
        return "https://www.youtube.com/@" + handle;
    }

    /**
     * Extract platform channel ID from channel URL.
     * For @handle URLs, uses the handle as the platform identifier.
     */
    private String extractChannelIdFromUrl(String url) {
        if (url == null) return null;
        if (url.contains("/channel/")) {
            return url.substring(url.lastIndexOf('/') + 1);
        }
        if (url.contains("/@")) {
            return url.substring(url.lastIndexOf("/@") + 2);
        }
        return url;
    }
}
