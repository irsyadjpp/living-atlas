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
public class KnowledgeExtracted extends BaseEvent {
    private UUID knowledgeObjectId;
    private String objectType;
    private String canonicalName;
    private String extractionModel;
    private Double confidenceScore;
}
