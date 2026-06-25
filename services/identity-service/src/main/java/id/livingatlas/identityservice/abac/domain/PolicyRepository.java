package id.livingatlas.identityservice.abac.domain;

import id.livingatlas.identityservice.abac.domain.model.Policy;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface PolicyRepository extends JpaRepository<Policy, UUID> {

    Optional<Policy> findByCode(String code);

    List<Policy> findAllByEnabledTrue();
}