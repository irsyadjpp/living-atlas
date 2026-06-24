package id.livingatlas.contentservice.story.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.sharedweb.exception.ApiException;
import id.livingatlas.contentservice.story.application.StoryService;
import id.livingatlas.contentservice.story.domain.Story;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/stories")
@RequiredArgsConstructor
public class StoryController {

    private final StoryService storyService;

    @PostMapping
    public ResponseEntity<ApiResponse<Story>> createStory(@RequestBody Story story) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(storyService.createStory(story)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Story>> getStory(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(storyService.getStory(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Story>> listStories(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(storyService.listStories(page, size, type, status)));
    }

    @PatchMapping("/{id}")
    public ResponseEntity<ApiResponse<Story>> updateStory(@PathVariable UUID id, @RequestBody Story story) {
        return ResponseEntity.ok(ApiResponse.success(storyService.updateStory(id, story)));
    }

    @PostMapping("/{id}/versions")
    public ResponseEntity<ApiResponse<id.livingatlas.contentservice.story.domain.StoryVersion>> createVersion(@PathVariable UUID id, @RequestBody id.livingatlas.contentservice.story.domain.StoryVersion version) {
        id.livingatlas.contentservice.story.domain.StoryVersion createdVersion = storyService.createVersion(id, version);
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(createdVersion));
    }

    @GetMapping("/{id}/versions")
    public ResponseEntity<ApiResponse<java.util.List<id.livingatlas.contentservice.story.domain.StoryVersion>>> listVersions(@PathVariable UUID id) {
        java.util.List<id.livingatlas.contentservice.story.domain.StoryVersion> versions = storyService.getVersions(id);
        return ResponseEntity.ok(ApiResponse.success(versions));
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteStory(@PathVariable UUID id) {
        storyService.deleteStory(id);
        return ResponseEntity.ok(ApiResponse.noContent());
    }
}
