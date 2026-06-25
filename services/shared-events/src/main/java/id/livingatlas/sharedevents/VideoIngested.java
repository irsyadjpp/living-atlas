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
public class VideoIngested extends BaseEvent {
    private UUID videoId;
    private String platformVideoId;
    private String title;
    private String platform;
    private UUID channelId;
}
