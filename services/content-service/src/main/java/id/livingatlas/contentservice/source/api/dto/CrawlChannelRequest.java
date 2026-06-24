package id.livingatlas.contentservice.source.api.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class CrawlChannelRequest {
    @NotBlank(message = "Channel handle, URL, or ID is required")
    private String handle;
    private Integer maxVideos = 50;
}