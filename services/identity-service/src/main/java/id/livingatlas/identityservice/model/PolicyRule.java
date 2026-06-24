package id.livingatlas.identityservice.model;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import java.time.OffsetDateTime;
import java.util.UUID;

@Entity
@Getter
@Setter
@ToString
@EqualsAndHashCode
@NoArgsConstructor
@Table(name = "policy_rules", schema = "iam")
public class PolicyRule {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "policy_id", nullable = false)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Policy policy;

    @Column(name = "rule_order", nullable = false)
    private Integer ruleOrder;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "rule_expression", columnDefinition = "jsonb", nullable = false)
    private String ruleExpression;

    @Setter(AccessLevel.NONE)
    @Column(name = "created_at", nullable = false, updatable = false)
    @CreationTimestamp
    private OffsetDateTime createdAt;

    public PolicyRule(Policy policy, Integer ruleOrder, String ruleExpression) {
        this.policy = policy;
        this.ruleOrder = ruleOrder;
        this.ruleExpression = ruleExpression;
    }
}