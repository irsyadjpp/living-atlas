package id.livingatlas.contentservice.article.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.contentservice.article.domain.Article;
import id.livingatlas.contentservice.article.infrastructure.ArticleRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ArticleService {

    private final ArticleRepository articleRepository;

    @Transactional
    public Article createArticle(Article article) {
        article.setStatus("draft");
        Article saved = articleRepository.save(article);
        log.info("Article created: id={}, type={}", saved.getId(), saved.getArticleType());
        return saved;
    }

    @Transactional(readOnly = true)
    public Article getArticle(UUID id) {
        return articleRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Article not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Article> listArticles(int page, int size, String type, String status) {
        return articleRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Article updateArticle(UUID id, Article updates) {
        Article article = getArticle(id);
        if (updates.getTitle() != null) article.setTitle(updates.getTitle());
        if (updates.getContent() != null) article.setContent(updates.getContent());
        return articleRepository.save(article);
    }

    @Transactional
    public void deleteArticle(UUID id) {
        articleRepository.deleteById(id);
        log.info("Article soft-deleted: id={}", id);
    }

    @Transactional
    public Article publishArticle(UUID id) {
        Article article = getArticle(id);
        article.setStatus("published");
        Article published = articleRepository.save(article);
        log.info("Article published: id={}", id);
        return published;
    }

    @Transactional
    public Article updateArticleStatus(UUID id, String status) {
        Article article = getArticle(id);
        article.setStatus(status);
        Article updated = articleRepository.save(article);
        log.info("Article status updated: id={}, status={}", id, status);
        return updated;
    }
}
