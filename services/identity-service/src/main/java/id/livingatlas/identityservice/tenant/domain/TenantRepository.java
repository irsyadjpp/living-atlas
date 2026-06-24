package id.livingatlas.identityservice.tenant.domain;

import id.livingatlas.identityservice.model.Tenant;
import id.livingatlas.identityservice.model.TenantStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface TenantRepository extends JpaRepository<Tenant, UUID> {

    Optional<Tenant> findBySlug(String slug);

    Page<Tenant> findAllByStatus(TenantStatus status, Pageable pageable);
}