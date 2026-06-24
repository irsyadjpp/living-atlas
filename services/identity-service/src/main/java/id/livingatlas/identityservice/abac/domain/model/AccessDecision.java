package id.livingatlas.identityservice.abac.domain.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AccessDecision {

    private boolean allowed;
    private String effect;
    private String policyCode;
    private String reason;
    private List<String> matchedRules;
}