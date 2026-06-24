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
public class ArticlePublished extends BaseEvent {
    private UUID articleId;
    private String slug;
    private String title;
    private String articleType;
    private UUID publishedBy;
}
