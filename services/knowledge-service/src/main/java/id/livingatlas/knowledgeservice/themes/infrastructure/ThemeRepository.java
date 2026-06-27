package id.livingatlas.knowledgeservice.themes.infrastructure;

import id.livingatlas.knowledgeservice.themes.domain.Theme;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface ThemeRepository extends JpaRepository<Theme, UUID> {
    Optional<Theme> findBySlug(String slug);
}