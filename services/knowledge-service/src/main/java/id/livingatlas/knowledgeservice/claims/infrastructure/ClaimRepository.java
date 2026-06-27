package id.livingatlas.knowledgeservice.claims.infrastructure;

import id.livingatlas.knowledgeservice.claims.domain.Claim;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

public interface ClaimRepository extends JpaRepository<Claim, UUID> {
    Page<Claim> findByStatus(String status, Pageable pageable);

    Page<Claim> findByEntityId(UUID entityId, Pageable pageable);
}