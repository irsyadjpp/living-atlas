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
public class EmbeddingCreated extends BaseEvent {
    private UUID embeddingId;
    private UUID objectId;
    private String objectType;
    private String embeddingModel;
    private Integer dimension;
}
