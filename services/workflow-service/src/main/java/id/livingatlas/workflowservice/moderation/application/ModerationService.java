package id.livingatlas.workflowservice.moderation.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.workflowservice.moderation.domain.Moderation;
import id.livingatlas.workflowservice.moderation.infrastructure.ModerationRepository;
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
public class ModerationService {

    private final ModerationRepository moderationRepository;

    @Transactional
    public Moderation createModeration(Moderation moderation) {
        moderation.setStatus("flagged");
        Moderation saved = moderationRepository.save(moderation);
        log.info("Moderation created: id={}, resourceType={}, resourceId={}, reason={}", 
                saved.getId(), saved.getResourceType(), saved.getResourceId(), saved.getFlagReason());
        return saved;
    }

    @Transactional(readOnly = true)
    public Moderation getModeration(UUID id) {
        return moderationRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Moderation not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Moderation> listModerations(int page, int size, String status) {
        if (status != null && !status.isEmpty()) {
            return new org.springframework.data.domain.PageImpl<>(
                moderationRepository.findByStatus(status),
                PageRequest.of(page, size),
                moderationRepository.findByStatus(status).size()
            );
        }
        return moderationRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Moderation resolve(UUID id, UUID moderatorId, String notes) {
        Moderation moderation = getModeration(id);
        moderation.setModeratorId(moderatorId);
        moderation.setStatus("resolved");
        moderation.setNotes(notes);
        moderation.setResolvedAt(OffsetDateTime.now());
        Moderation updated = moderationRepository.save(moderation);
        log.info("Moderation resolved: id={}, moderatorId={}", id, moderatorId);
        return updated;
    }

    @Transactional
    public Moderation flag(UUID id, String flagReason, String notes) {
        Moderation moderation = getModeration(id);
        moderation.setStatus("flagged");
        moderation.setFlagReason(flagReason);
        moderation.setNotes(notes);
        Moderation updated = moderationRepository.save(moderation);
        log.info("Moderation flagged: id={}, reason={}", id, flagReason);
        return updated;
    }
}