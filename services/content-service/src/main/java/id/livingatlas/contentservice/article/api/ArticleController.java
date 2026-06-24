package id.livingatlas.contentservice.article.api;

import id.livingatlas.sharedweb.response.ApiResponse;
import id.livingatlas.sharedweb.response.PagedResponse;
import id.livingatlas.contentservice.article.application.ArticleService;
import id.livingatlas.contentservice.article.domain.Article;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/v1/articles")
@RequiredArgsConstructor
public class ArticleController {

    private final ArticleService articleService;

    @PostMapping
    public ResponseEntity<ApiResponse<Article>> createArticle(@RequestBody Article article) {
        return ResponseEntity.status(HttpStatus.CREATED).body(ApiResponse.created(articleService.createArticle(article)));
    }

    @GetMapping("/{id}")
    public ResponseEntity<ApiResponse<Article>> getArticle(@PathVariable UUID id) {
        return ResponseEntity.ok(ApiResponse.success(articleService.getArticle(id)));
    }

    @GetMapping
    public ResponseEntity<PagedResponse<Article>> listArticles(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(required = false) String type,
            @RequestParam(required = false) String status) {
        return ResponseEntity.ok(PagedResponse.from(articleService.listArticles(page, size, type, status)));
    }
}
