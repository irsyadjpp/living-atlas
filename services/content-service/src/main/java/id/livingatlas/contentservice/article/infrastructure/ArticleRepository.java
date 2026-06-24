package id.livingatlas.contentservice.article.infrastructure;

import id.livingatlas.contentservice.article.domain.Article;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface ArticleRepository extends JpaRepository<Article, UUID> {
    Page<Article> findByStatus(String status, Pageable pageable);
    Page<Article> findByTenantId(UUID tenantId, Pageable pageable);
}