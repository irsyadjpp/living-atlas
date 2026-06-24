package id.livingatlas.contentservice.source.infrastructure;

import id.livingatlas.contentservice.source.domain.Source;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface SourceRepository extends JpaRepository<Source, UUID> {
    Optional<Source> findByPlatformVideoId(String platformVideoId);
    Page<Source> findByChannelId(UUID channelId, Pageable pageable);
    Page<Source> findByStatus(String status, Pageable pageable);
}