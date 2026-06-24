package id.livingatlas.identityservice.abac.application;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import id.livingatlas.identityservice.abac.domain.PolicyRepository;
import id.livingatlas.identityservice.abac.domain.PolicyRuleRepository;
import id.livingatlas.identityservice.abac.domain.model.AccessDecision;
import id.livingatlas.identityservice.model.Policy;
import id.livingatlas.identityservice.model.PolicyRule;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AbacService {

    private final PolicyRepository policyRepository;
    private final PolicyRuleRepository policyRuleRepository;
    private final ObjectMapper objectMapper;

    @Transactional
    public Policy createPolicy(String code, String name, String effect, String description) {
        Policy policy = new Policy(code, name, effect);
        policy.setDescription(description);
        return policyRepository.save(policy);
    }

    @Transactional
    public Policy updatePolicy(UUID policyId, String name, String description) {
        Policy policy = policyRepository.findById(policyId)
                .orElseThrow(() -> new IllegalArgumentException("Policy not found: " + policyId));
        if (name != null) policy.setName(name);
        if (description != null) policy.setDescription(description);
        return policyRepository.save(policy);
    }

    @Transactional
    public void togglePolicy(UUID policyId, boolean enabled) {
        Policy policy = policyRepository.findById(policyId)
                .orElseThrow(() -> new IllegalArgumentException("Policy not found: " + policyId));
        policy.setEnabled(enabled);
        policyRepository.save(policy);
    }

    @Transactional
    public PolicyRule addRuleToPolicy(UUID policyId, Integer ruleOrder, String ruleExpression) {
        Policy policy = policyRepository.findById(policyId)
                .orElseThrow(() -> new IllegalArgumentException("Policy not found: " + policyId));
        PolicyRule rule = new PolicyRule(policy, ruleOrder, ruleExpression);
        return policyRuleRepository.save(rule);
    }

    @Transactional(readOnly = true)
    public List<Policy> getAllPolicies() {
        return policyRepository.findAll();
    }

    @Transactional(readOnly = true)
    public Policy getPolicy(UUID policyId) {
        return policyRepository.findById(policyId)
                .orElseThrow(() -> new IllegalArgumentException("Policy not found: " + policyId));
    }

    @Transactional(readOnly = true)
    public AccessDecision evaluateAccess(
            UUID userId, String resourceType, String resourceId,
            String action, Map<String, Object> additionalAttributes) {

        List<Policy> enabledPolicies = policyRepository.findAllByEnabledTrue();

        for (Policy policy : enabledPolicies) {
            List<PolicyRule> rules = policyRuleRepository.findAllByPolicyIdOrderByRuleOrder(policy.getId());

            boolean allRulesMatch = rules.stream().allMatch(rule -> {
                try {
                    return evaluateRule(rule, userId, resourceType, resourceId, action, additionalAttributes);
                } catch (Exception e) {
                    log.warn("Error evaluating rule {}: {}", rule.getId(), e.getMessage());
                    return false;
                }
            });

            if (allRulesMatch && !rules.isEmpty()) {
                List<String> matchedRuleIds = rules.stream()
                        .map(r -> r.getId().toString())
                        .collect(Collectors.toList());

                return AccessDecision.builder()
                        .allowed("allow".equalsIgnoreCase(policy.getEffect()))
                        .effect(policy.getEffect())
                        .policyCode(policy.getCode())
                        .reason("Matched policy: " + policy.getName())
                        .matchedRules(matchedRuleIds)
                        .build();
            }
        }

        return AccessDecision.builder()
                .allowed(false)
                .effect("deny")
                .reason("No matching policy found - default deny")
                .build();
    }

    @Transactional(readOnly = true)
    public boolean canAccess(UUID userId, String resourceType, String resourceId,
                              String action, Map<String, Object> attributes) {
        return evaluateAccess(userId, resourceType, resourceId, action, attributes).isAllowed();
    }

    private boolean evaluateRule(PolicyRule rule, UUID userId, String resourceType,
                                  String resourceId, String action,
                                  Map<String, Object> additionalAttributes) throws Exception {

        Map<String, Object> expression = objectMapper.readValue(
                rule.getRuleExpression(), new TypeReference<Map<String, Object>>() {});

        for (Map.Entry<String, Object> entry : expression.entrySet()) {
            String key = entry.getKey();
            Object expectedValue = entry.getValue();

            Object actualValue = resolveAttribute(key, userId, resourceType, resourceId, action, additionalAttributes);

            if (actualValue == null || !actualValue.toString().equalsIgnoreCase(expectedValue.toString())) {
                return false;
            }
        }

        return true;
    }

    private Object resolveAttribute(String key, UUID userId, String resourceType,
                                     String resourceId, String action,
                                     Map<String, Object> additionalAttributes) {
        return switch (key) {
            case "subject.id" -> userId.toString();
            case "resource.type" -> resourceType;
            case "resource.id" -> resourceId;
            case "action" -> action;
            default -> {
                if (key.startsWith("subject.")) {
                    yield additionalAttributes.getOrDefault(key.substring(8), null);
                } else if (key.startsWith("resource.")) {
                    yield additionalAttributes.getOrDefault(key.substring(9), null);
                } else {
                    yield additionalAttributes.getOrDefault(key, null);
                }
            }
        };
    }
}