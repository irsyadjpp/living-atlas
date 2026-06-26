package id.livingatlas.sharedweb.abac;

import id.livingatlas.sharedweb.abac.model.PolicyRule;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface PolicyRuleRepository extends JpaRepository<PolicyRule, UUID> {

    List<PolicyRule> findAllByPolicyIdOrderByRuleOrder(UUID policyId);

    List<PolicyRule> findAllByPolicyIdIn(List<UUID> policyIds);
}