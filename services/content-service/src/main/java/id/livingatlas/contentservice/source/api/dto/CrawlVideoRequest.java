package id.livingatlas.contentservice.source.api.dto;

import jakarta.validation.constraints.AssertTrue;
import lombok.Data;

@Data
public class CrawlVideoRequest {
    private String platformVideoId;
    private String url;

    @AssertTrue(message = "Either platformVideoId or url must be provided")
    public boolean isValid() {
        return platformVideoId != null && !platformVideoId.isBlank()
            || url != null && !url.isBlank();
    }
}