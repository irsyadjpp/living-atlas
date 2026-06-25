package id.livingatlas.knowledgeservice.claims.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.knowledgeservice.claims.domain.Claim;
import id.livingatlas.knowledgeservice.claims.infrastructure.ClaimRepository;
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
public class ClaimService {

    private final ClaimRepository claimRepository;

    @Transactional
    public Claim createClaim(Claim claim) {
        claim.setStatus("extracted");
        Claim saved = claimRepository.save(claim);
        log.info("Claim created: id={}, type={}", saved.getId(), saved.getClaimType());
        return saved;
    }

    @Transactional(readOnly = true)
    public Claim getClaim(UUID id) {
        return claimRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Claim not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Claim> listClaims(int page, int size, String status, UUID entityId) {
        return claimRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public void verifyClaim(UUID id) {
        Claim claim = getClaim(id);
        claim.setStatus("verified");
        claimRepository.save(claim);
        log.info("Claim verified: id={}", id);
    }

    @Transactional
    public void rejectClaim(UUID id) {
        Claim claim = getClaim(id);
        claim.setStatus("rejected");
        claimRepository.save(claim);
        log.info("Claim rejected: id={}", id);
    }
}