package id.livingatlas.sharedevents;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@NoArgsConstructor
@AllArgsConstructor
@EqualsAndHashCode(callSuper = true)
public class TranscriptGenerated extends BaseEvent {
    private UUID transcriptId;
    private UUID videoId;
    private String transcriptType;
    private String languageCode;
    private Integer wordCount;
}
