package id.livingatlas.workflowservice.approval.infrastructure;

import id.livingatlas.workflowservice.approval.domain.Approval;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface ApprovalRepository extends JpaRepository<Approval, UUID> {
    Optional<Approval> findByResourceTypeAndResourceId(String resourceType, UUID resourceId);
    java.util.List<Approval> findByStatus(String status);
}