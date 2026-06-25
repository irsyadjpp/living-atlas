package id.livingatlas.identityservice.apikeys.infrastructure;

import id.livingatlas.identityservice.apikeys.domain.ApiKey;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ApiKeyRepository extends JpaRepository<ApiKey, UUID> {
    Optional<ApiKey> findByApiKey(String apiKey);
    java.util.List<ApiKey> findByUserId(UUID userId);
}