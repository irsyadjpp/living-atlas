package id.livingatlas.identityservice.apikeys.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.identityservice.apikeys.domain.ApiKey;
import id.livingatlas.identityservice.apikeys.infrastructure.ApiKeyRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.OffsetDateTime;
import java.util.UUID;

@Service
@RequiredArgsConstructor
@Slf4j
public class ApiKeyService {

    private final ApiKeyRepository apiKeyRepository;

    @Transactional
    public ApiKey createApiKey(ApiKey apiKey) {
        apiKey.setStatus("active");
        ApiKey saved = apiKeyRepository.save(apiKey);
        log.info("ApiKey created: id={}, userId={}, name={}", 
                saved.getId(), saved.getUserId(), saved.getName());
        return saved;
    }

    @Transactional(readOnly = true)
    public ApiKey getApiKey(UUID id) {
        return apiKeyRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("ApiKey not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<ApiKey> listApiKeys(int page, int size, UUID userId) {
        if (userId != null) {
            return new org.springframework.data.domain.PageImpl<>(
                apiKeyRepository.findByUserId(userId),
                PageRequest.of(page, size),
                apiKeyRepository.findByUserId(userId).size()
            );
        }
        return apiKeyRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public ApiKey updateLastUsed(UUID id) {
        ApiKey apiKey = getApiKey(id);
        apiKey.setLastUsedAt(OffsetDateTime.now());
        return apiKeyRepository.save(apiKey);
    }

    @Transactional
    public void deleteApiKey(UUID id) {
        apiKeyRepository.deleteById(id);
        log.info("ApiKey deleted: id={}", id);
    }
}