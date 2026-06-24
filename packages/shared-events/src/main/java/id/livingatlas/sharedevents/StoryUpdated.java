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
public class StoryUpdated extends BaseEvent {
    private UUID storyId;
    private String slug;
    private String title;
    private Integer versionNumber;
    private UUID updatedBy;
}
