"""
Knowledge Validator — AI Platform

Assesses knowledge quality:
- Schema validation (required fields, types, formats)
- Confidence scoring (extraction, validation, composite)
- Missing data detection
- Contradiction review
- Research gap identification

Consumes: knowledge.validation.requested (from orchestration-service)
Produces: knowledge.validated (to orchestration-service + knowledge-service)
"""

import json
import structlog
import time
from typing import Optional
from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime, timezone

logger = structlog.get_logger(__name__)


@dataclass
class ValidationResult:
    knowledgeId: str
    canonicalStoryId: str
    sourceId: str
    jobId: str
    validatedAt: str
    validationResult: dict
    warnings: list
    issues: list
    validationMetadata: dict


class KnowledgeValidator:
    """
    Validates knowledge quality across multiple dimensions:
    - Schema compliance
    - Evidence sufficiency
    - Confidence calibration
    - Cross-entity consistency
    - Contradiction detection
    """

    # Required fields per entity type
    REQUIRED_FIELDS = {
        "entity": ["entityId", "name", "entityType", "confidence"],
        "claim": ["claimId", "statement", "confidence", "evidence"],
        "theme": ["themeId", "name", "confidence"],
        "motif": ["motifId", "name", "motifType", "confidence"],
        "belief": ["beliefId", "statement", "adherentCommunity", "confidence"],
        "ritual": ["ritualId", "name", "description", "confidence"],
    }

    # Minimum evidence segments per confidence level
    MIN_EVIDENCE_THRESHOLDS = {
        0: 0,    # 0-20 confidence: no minimum
        20: 1,   # 21-40: at least 1 evidence
        40: 1,   # 41-60: at least 1 evidence
        60: 2,   # 61-80: at least 2 evidence
        80: 3,   # 81-100: at least 3 evidence
    }

    def __init__(self, llm_router=None):
        self.llm_router = llm_router

    async def validate(self, knowledge: dict, job_config: dict) -> ValidationResult:
        """
        Main validation entry point.
        
        1. Schema validation
        2. Evidence sufficiency check
        3. Confidence calibration
        4. Consistency check
        5. Contradiction detection
        6. Research gap identification
        7. Generate quality score
        """
        job_id = job_config.get("jobId", str(uuid4()))
        start_time = time.time()

        entities = knowledge.get("entities", [])
        claims = knowledge.get("claims", [])
        themes = knowledge.get("themes", [])
        motifs = knowledge.get("motifs", [])
        beliefs = knowledge.get("beliefs", [])
        rituals = knowledge.get("rituals", [])
        contradictions = knowledge.get("contradictions", [])

        warnings = []
        issues = []

        # Stage 1: Schema validation
        schema_issues = self._validate_schema(entities, claims, themes, motifs, beliefs, rituals)
        issues.extend(schema_issues)

        # Stage 2: Evidence sufficiency
        evidence_warnings = self._check_evidence_sufficiency(claims, entities)
        warnings.extend(evidence_warnings)

        # Stage 3: Confidence calibration
        confidence_warnings = self._calibrate_confidence(claims, entities, themes, motifs)
        warnings.extend(confidence_warnings)

        # Stage 4: Consistency check
        consistency_warnings = self._check_consistency(entities, claims)
        warnings.extend(consistency_warnings)

        # Stage 5: Contradiction review
        contradiction_warnings = self._review_contradictions(contradictions)
        warnings.extend(contradiction_warnings)

        # Stage 6: Research gap identification
        gap_issues = self._identify_research_gaps(knowledge)
        warnings.extend(gap_issues)

        # Stage 7: Quality scoring
        quality_scores = self._calculate_quality_scores(
            entities=entities,
            claims=claims,
            themes=themes,
            motifs=motifs,
            schema_issues=len(schema_issues),
            evidence_warnings=len(evidence_warnings),
            total_warnings=len(warnings),
            total_issues=len(issues)
        )

        elapsed = int((time.time() - start_time) * 1000)

        return ValidationResult(
            knowledgeId=knowledge.get("knowledgeId", str(uuid4())),
            canonicalStoryId=knowledge.get("canonicalStoryId", ""),
            sourceId=knowledge.get("sourceId", ""),
            jobId=job_id,
            validatedAt=datetime.now(timezone.utc).isoformat(),
            validationResult={
                "overallScore": quality_scores["overall"],
                "passed": quality_scores["overall"] >= 0.6,
                "schemaValid": len(schema_issues) == 0,
                "completenessScore": quality_scores["completeness"],
                "confidenceScore": quality_scores["confidence"],
                "consistencyScore": quality_scores["consistency"],
            },
            warnings=warnings[:20],  # Limit to 20 warnings
            issues=issues[:10],      # Limit to 10 issues
            validationMetadata={
                "modelUsed": job_config.get("model", "rule-based"),
                "promptVersion": job_config.get("promptVersion", "knowledge-validation-v1"),
                "inputTokens": 0,
                "outputTokens": 0,
                "executionCost": 0.0,
                "executionTimeMs": elapsed,
            }
        )

    def _validate_schema(self, entities, claims, themes, motifs, beliefs, rituals) -> list:
        """Validate that all knowledge objects have required fields."""
        issues = []

        for entity in entities:
            missing = self._missing_fields(entity, "entity")
            if missing:
                issues.append({
                    "type": "missing_field",
                    "target": "entity",
                    "targetId": entity.get("entityId", "unknown"),
                    "message": f"Entity missing required fields: {', '.join(missing)}",
                    "severity": "high"
                })
            # Validate entity type
            valid_types = ["spirit", "deity", "creature", "person", "location", 
                          "object", "phenomenon", "concept", "group", "other"]
            etype = entity.get("entityType")
            if etype and etype not in valid_types:
                issues.append({
                    "type": "invalid_entity_type",
                    "target": "entity",
                    "targetId": entity.get("entityId", "unknown"),
                    "message": f"Invalid entity type '{etype}'. Must be one of: {', '.join(valid_types)}",
                    "severity": "medium"
                })

        for claim in claims:
            missing = self._missing_fields(claim, "claim")
            if missing:
                issues.append({
                    "type": "missing_field",
                    "target": "claim",
                    "targetId": claim.get("claimId", "unknown"),
                    "message": f"Claim missing required fields: {', '.join(missing)}",
                    "severity": "high"
                })
            # Validate claim category
            valid_categories = ["existence", "behavior", "appearance", "location",
                               "history", "origin", "power", "relationship", "ritual", "belief"]
            category = claim.get("category")
            if category and category not in valid_categories:
                issues.append({
                    "type": "invalid_category",
                    "target": "claim",
                    "targetId": claim.get("claimId", "unknown"),
                    "message": f"Invalid claim category '{category}'",
                    "severity": "low"
                })

        for theme in themes:
            missing = self._missing_fields(theme, "theme")
            if missing:
                issues.append({
                    "type": "missing_field",
                    "target": "theme",
                    "targetId": theme.get("themeId", "unknown"),
                    "message": f"Theme missing required fields: {', '.join(missing)}",
                    "severity": "medium"
                })

        return issues

    def _missing_fields(self, obj: dict, obj_type: str) -> list:
        """Check for missing required fields."""
        required = self.REQUIRED_FIELDS.get(obj_type, [])
        return [f for f in required if f not in obj or obj.get(f) is None]

    def _check_evidence_sufficiency(self, claims: list, entities: list) -> list:
        """Check that claims and entities have sufficient evidence."""
        warnings = []

        for claim in claims:
            evidence = claim.get("evidence", [])
            confidence = claim.get("confidence", 0)
            required_count = self._get_min_evidence(confidence)
            
            if len(evidence) < required_count:
                warnings.append({
                    "type": "insufficient_evidence",
                    "target": "claim",
                    "targetId": claim.get("claimId", "unknown"),
                    "message": (
                        f"Claim has {len(evidence)} evidence segments, "
                        f"expected at least {required_count} for confidence {confidence}"
                    ),
                    "severity": "medium" if required_count > 1 else "low"
                })

        for entity in entities:
            evidence = entity.get("evidence", [])
            if not evidence:
                warnings.append({
                    "type": "missing_evidence",
                    "target": "entity",
                    "targetId": entity.get("entityId", "unknown"),
                    "message": f"Entity '{entity.get('name', 'unknown')}' has no evidence",
                    "severity": "medium"
                })

        return warnings

    def _get_min_evidence(self, confidence: int) -> int:
        """Get minimum evidence count for a confidence level."""
        threshold = 0
        for level, count in sorted(self.MIN_EVIDENCE_THRESHOLDS.items()):
            if confidence >= level:
                threshold = count
        return threshold

    def _calibrate_confidence(self, claims: list, entities: list, 
                               themes: list, motifs: list) -> list:
        """Check confidence score calibration."""
        warnings = []

        for claim in claims:
            confidence = claim.get("confidence", 0)
            evidence_count = len(claim.get("evidence", []))
            
            # High confidence with single evidence is suspicious
            if confidence >= 80 and evidence_count < 2:
                warnings.append({
                    "type": "confidence_mismatch",
                    "target": "claim",
                    "targetId": claim.get("claimId", "unknown"),
                    "message": f"Confidence {confidence} is high but only {evidence_count} evidence(s) provided",
                    "severity": "medium"
                })
            
            # Low confidence with no evidence
            if confidence < 20 and evidence_count == 0:
                warnings.append({
                    "type": "low_confidence_no_evidence",
                    "target": "claim",
                    "targetId": claim.get("claimId", "unknown"),
                    "message": f"Claim has low confidence ({confidence}) and no evidence",
                    "severity": "low"
                })

        for entity in entities:
            confidence = entity.get("confidence", 0)
            evidence_count = len(entity.get("evidence", []))
            
            if confidence >= 90 and evidence_count == 0:
                warnings.append({
                    "type": "confidence_mismatch",
                    "target": "entity",
                    "targetId": entity.get("entityId", "unknown"),
                    "message": f"Entity confidence {confidence} with zero evidence",
                    "severity": "high"
                })

        return warnings

    def _check_consistency(self, entities: list, claims: list) -> list:
        """Check cross-entity and entity-claim consistency."""
        warnings = []

        # Build entity ID set
        entity_ids = {e.get("entityId") for e in entities if e.get("entityId")}
        entity_names = {e.get("entityId"): e.get("name", "") for e in entities}

        # Check claim entity references
        for claim in claims:
            claim_entity_ids = claim.get("entityIds", [])
            for eid in claim_entity_ids:
                if eid not in entity_ids:
                    warnings.append({
                        "type": "orphaned_entity_reference",
                        "target": "claim",
                        "targetId": claim.get("claimId", "unknown"),
                        "message": f"Claim references entity {eid} which is not in entities list",
                        "severity": "medium"
                    })

        # Check for duplicate entity names (possible unresolved aliases)
        name_counts = {}
        for entity in entities:
            name = entity.get("normalizedName", entity.get("name", "")).lower()
            name_counts[name] = name_counts.get(name, 0) + 1

        duplicates = {name: count for name, count in name_counts.items() if count > 1}
        for name, count in duplicates.items():
            warnings.append({
                "type": "possible_duplicate",
                "target": "entity",
                "targetId": "multiple",
                "message": f"Entity name '{name}' appears {count} times, may need normalization merge",
                "severity": "low"
            })

        return warnings

    def _review_contradictions(self, contradictions: list) -> list:
        """Review contradictions for completeness."""
        warnings = []

        for contradiction in contradictions:
            sides = contradiction.get("sides", [])
            if len(sides) < 2:
                warnings.append({
                    "type": "incomplete_contradiction",
                    "target": "contradiction",
                    "targetId": contradiction.get("contradictionId", "unknown"),
                    "message": f"Contradiction has only {len(sides)} side(s), expected at least 2",
                    "severity": "high"
                })
            
            for side in sides:
                if not side.get("evidence"):
                    warnings.append({
                        "type": "missing_evidence",
                        "target": "contradiction",
                        "targetId": contradiction.get("contradictionId", "unknown"),
                        "message": f"Contradiction side '{side.get('label', 'unknown')}' has no evidence",
                        "severity": "medium"
                    })

        return warnings

    def _identify_research_gaps(self, knowledge: dict) -> list:
        """Identify research gaps in the knowledge."""
        warnings = []
        entities = knowledge.get("entities", [])
        claims = knowledge.get("claims", [])
        themes = knowledge.get("themes", [])
        rituals = knowledge.get("rituals", [])
        beliefs = knowledge.get("beliefs", [])

        # Gap: Entity without cultural context
        for entity in entities:
            if not entity.get("culturalContext") or not entity.get("culturalContext", {}).get("region"):
                if entity.get("entityType") in ("spirit", "deity", "creature"):
                    warnings.append({
                        "type": "research_gap",
                        "target": "entity",
                        "targetId": entity.get("entityId", "unknown"),
                        "message": f"Entity '{entity.get('name', 'unknown')}' missing cultural context (region)",
                        "severity": "medium"
                    })

        # Gap: No themes extracted
        if not themes and entities:
            warnings.append({
                "type": "research_gap",
                "target": "story",
                "targetId": "overall",
                "message": "No themes extracted despite having entities",
                "severity": "low"
            })

        # Gap: Story mentions beliefs but no rituals
        if beliefs and not rituals:
            warnings.append({
                "type": "research_gap",
                "target": "story",
                "targetId": "overall",
                "message": "Beliefs present but no associated rituals extracted",
                "severity": "low"
            })

        # Gap: Single witness account
        witnesses_seen = set()
        for claim in claims:
            for evidence in claim.get("evidence", []):
                speaker = evidence.get("speaker")
                if speaker:
                    witnesses_seen.add(speaker)
        
        if len(witnesses_seen) <= 1 and len(claims) > 0:
            warnings.append({
                "type": "research_gap",
                "target": "story",
                "targetId": "overall",
                "message": f"Only {len(witnesses_seen)} speaker(s) identified; corroboration recommended",
                "severity": "medium"
            })

        return warnings

    def _calculate_quality_scores(self, entities, claims, themes, motifs,
                                    schema_issues, evidence_warnings,
                                    total_warnings, total_issues) -> dict:
        """Calculate quality scores across multiple dimensions."""
        
        # Completeness score (0.0 - 1.0)
        has_entities = len(entities) > 0
        has_claims = len(claims) > 0
        has_themes = len(themes) > 0
        has_motifs = len(motifs) > 0
        
        completeness = (
            0.30 * (1 if has_entities else 0) +
            0.30 * (1 if has_claims else 0) +
            0.20 * (1 if has_themes else 0) +
            0.20 * (1 if has_motifs else 0)
        )

        # Confidence score (0.0 - 1.0)
        all_confidences = []
        for claim in claims:
            all_confidences.append(claim.get("confidence", 0) / 100.0)
        for entity in entities:
            all_confidences.append(entity.get("confidence", 0) / 100.0)
        
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        # Consistency score (0.0 - 1.0)
        consistency = 1.0 - (total_warnings * 0.05)
        consistency = max(0.0, min(1.0, consistency))

        # Schema compliance
        schema_compliance = 1.0 - (total_issues * 0.1)
        schema_compliance = max(0.0, min(1.0, schema_compliance))

        # Overall score (weighted)
        overall = (
            completeness * 0.25 +
            avg_confidence * 0.25 +
            consistency * 0.20 +
            schema_compliance * 0.20 +
            (1.0 - (evidence_warnings * 0.05)) * 0.10
        )
        overall = max(0.0, min(1.0, overall))

        return {
            "overall": round(overall, 4),
            "completeness": round(completeness, 4),
            "confidence": round(avg_confidence, 4),
            "consistency": round(consistency, 4),
        }