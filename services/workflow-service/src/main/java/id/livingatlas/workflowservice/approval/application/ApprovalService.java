package id.livingatlas.workflowservice.approval.application;
import id.livingatlas.sharedweb.exception.ApiException;

import id.livingatlas.workflowservice.approval.domain.Approval;
import id.livingatlas.workflowservice.approval.infrastructure.ApprovalRepository;
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
public class ApprovalService {

    private final ApprovalRepository approvalRepository;

    @Transactional
    public Approval createApproval(Approval approval) {
        approval.setStatus("pending");
        Approval saved = approvalRepository.save(approval);
        log.info("Approval created: id={}, resourceType={}, resourceId={}", 
                saved.getId(), saved.getResourceType(), saved.getResourceId());
        return saved;
    }

    @Transactional(readOnly = true)
    public Approval getApproval(UUID id) {
        return approvalRepository.findById(id)
                .orElseThrow(() -> ApiException.notFound("Approval not found: " + id));
    }

    @Transactional(readOnly = true)
    public Page<Approval> listApprovals(int page, int size, String status) {
        if (status != null && !status.isEmpty()) {
            return new org.springframework.data.domain.PageImpl<>(
                approvalRepository.findByStatus(status),
                PageRequest.of(page, size),
                approvalRepository.findByStatus(status).size()
            );
        }
        return approvalRepository.findAll(PageRequest.of(page, size));
    }

    @Transactional
    public Approval approve(UUID id, UUID approverId, String notes) {
        Approval approval = getApproval(id);
        approval.setApproverId(approverId);
        approval.setStatus("approved");
        approval.setNotes(notes);
        approval.setReviewedAt(OffsetDateTime.now());
        Approval updated = approvalRepository.save(approval);
        log.info("Approval approved: id={}, approverId={}", id, approverId);
        return updated;
    }

    @Transactional
    public Approval reject(UUID id, UUID approverId, String notes) {
        Approval approval = getApproval(id);
        approval.setApproverId(approverId);
        approval.setStatus("rejected");
        approval.setNotes(notes);
        approval.setReviewedAt(OffsetDateTime.now());
        Approval updated = approvalRepository.save(approval);
        log.info("Approval rejected: id={}, approverId={}", id, approverId);
        return updated;
    }
}