"""
Knowledge Normalizer — AI Platform

Resolves ambiguity in extracted knowledge:
- Alias detection (Kuntilanak ↔ Pontianak ↔ Kunti)
- Duplicate detection and merging
- Entity normalization
- Cultural normalization
- Folklore normalization

Consumes: knowledge.normalization.requested (from orchestration-service)
Produces: knowledge.normalized (to orchestration-service + knowledge-service)
"""

import json
import structlog
import time
from typing import Optional
from dataclasses import dataclass, field
from uuid import uuid4

logger = structlog.get_logger(__name__)


@dataclass
class NormalizationResult:
    knowledgeId: str
    canonicalStoryId: str
    sourceId: str
    jobId: str
    normalizedKnowledge: dict
    normalizationReport: dict
    normalizationMetadata: dict


class KnowledgeNormalizer:
    """
    Normalizes extracted knowledge by resolving aliases, merging duplicates,
    and standardizing entity names across Indonesian folklore traditions.
    """

    # Known alias mappings for Indonesian folklore entities
    # This is a bootstrap dictionary; the AI provider expands it dynamically
    KNOWN_ALIASES = {
        "kuntilanak": ["pontianak", "kunti", "hantu perempuan"],
        "genderuwo": ["gendruwo", "genderuwo", "hantu bodoh"],
        "pocong": ["hantu pocong", "mayat terbungkus"],
        "tuyul": ["tuyul", "hantu anak kecil"],
        "wewe": ["wewe gombel", "gandarwa"],
        "leak": ["leyak", "leak bali"],
        "babi ngepet": ["babi ngepet", "celeng"],
        "jelangkung": ["jelangkung", "boneka arwah"],
    }

    def __init__(self, llm_router=None):
        self.llm_router = llm_router

    async def normalize(self, knowledge: dict, job_config: dict) -> NormalizationResult:
        """
        Main normalization entry point.
        
        1. Detect aliases across all entities
        2. Merge duplicate entities
        3. Normalize entity names to canonical forms
        4. Resolve cultural naming conflicts
        5. Generate normalization report
        """
        job_id = job_config.get("jobId", str(uuid4()))
        start_time = time.time()

        entities = knowledge.get("entities", [])
        themes = knowledge.get("themes", [])
        motifs = knowledge.get("motifs", [])
        claims = knowledge.get("claims", [])

        # Stage 1: Alias detection
        alias_map = await self._detect_aliases(entities)
        
        # Stage 2: Duplicate detection and merging
        merged_entities, merge_log = self._merge_duplicates(entities, alias_map)
        
        # Stage 3: Name normalization
        normalized_entities = self._normalize_names(merged_entities, alias_map)
        
        # Stage 4: Update claims with merged entity IDs
        normalized_claims = self._update_claim_entity_refs(claims, merge_log)
        
        # Stage 5: Cultural context normalization
        normalized_entities = self._normalize_cultural_context(normalized_entities)

        elapsed = int((time.time() - start_time) * 1000)

        normalization_report = {
            "entityAliases": alias_map,
            "mergedEntities": [
                {
                    "targetId": merge["target"],
                    "sourceIds": merge["sources"],
                    "mergeReason": merge["reason"]
                }
                for merge in merge_log
            ],
            "totalAliasesResolved": sum(len(v) for v in alias_map.values()),
            "totalDuplicatesMerged": len(merge_log)
        }

        normalized_knowledge = {
            "themes": themes,
            "entities": normalized_entities,
            "claims": normalized_claims,
            "motifs": motifs,
            "rituals": knowledge.get("rituals", []),
            "beliefs": knowledge.get("beliefs", []),
            "contradictions": knowledge.get("contradictions", []),
            "normalizationReport": normalization_report
        }

        return NormalizationResult(
            knowledgeId=knowledge.get("knowledgeId", str(uuid4())),
            canonicalStoryId=knowledge.get("canonicalStoryId", ""),
            sourceId=knowledge.get("sourceId", ""),
            jobId=job_id,
            normalizedKnowledge=normalized_knowledge,
            normalizationReport=normalization_report,
            normalizationMetadata={
                "modelUsed": job_config.get("model", "rule-based"),
                "promptVersion": job_config.get("promptVersion", "knowledge-normalization-v1"),
                "inputTokens": 0,
                "outputTokens": 0,
                "executionCost": 0.0,
                "executionTimeMs": elapsed,
                "aliasesResolved": sum(len(v) for v in alias_map.values()),
                "duplicatesMerged": len(merge_log)
            }
        )

    async def _detect_aliases(self, entities: list) -> dict:
        """
        Detect aliases by comparing entity names against known mappings
        and using AI provider for unknown entities.
        """
        alias_map = {}
        entity_names = [e.get("name", "").lower().strip() for e in entities if e.get("name")]
        
        for name in entity_names:
            resolved = False
            for canonical, aliases in self.KNOWN_ALIASES.items():
                if name == canonical or name in aliases:
                    if canonical not in alias_map:
                        alias_map[canonical] = set()
                    alias_map[canonical].add(name)
                    resolved = True
                    break
            
            if not resolved:
                # Unknown entity — flag for AI-based alias detection
                alias_map[name] = set()

        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in alias_map.items()}

    def _merge_duplicates(self, entities: list, alias_map: dict) -> tuple:
        """Merge entities that are aliases of the same canonical entity."""
        merged = []
        merge_log = []
        seen_canonical = {}

        for entity in entities:
            name = entity.get("name", "").lower().strip()
            
            # Find canonical name for this entity
            canonical = self._resolve_canonical(name, alias_map)
            
            if canonical in seen_canonical:
                # Merge into existing entity
                target_idx = seen_canonical[canonical]
                target = merged[target_idx]
                
                # Merge evidence
                target_evidence = target.get("evidence", [])
                source_evidence = entity.get("evidence", [])
                target["evidence"] = target_evidence + [
                    e for e in source_evidence 
                    if e not in target_evidence
                ]
                
                # Merge aliases
                target_aliases = target.get("aliases", [])
                source_name = entity.get("name")
                if source_name and source_name not in target_aliases:
                    target_aliases.append(source_name)
                target["aliases"] = target_aliases
                
                # Take max confidence
                target["confidence"] = max(
                    target.get("confidence", 0),
                    entity.get("confidence", 0)
                )
                
                merge_log.append({
                    "target": target["entityId"],
                    "sources": [entity["entityId"]],
                    "reason": "alias_merge"
                })
            else:
                seen_canonical[canonical] = len(merged)
                # Set normalized name
                entity["normalizedName"] = canonical
                merged.append(entity)

        return merged, merge_log

    def _resolve_canonical(self, name: str, alias_map: dict) -> str:
        """Resolve an entity name to its canonical form."""
        name_lower = name.lower().strip()
        
        for canonical, aliases in alias_map.items():
            if name_lower == canonical.lower() or name_lower in [a.lower() for a in aliases]:
                return canonical
        
        return name

    def _normalize_names(self, entities: list, alias_map: dict) -> list:
        """Normalize entity names to standard forms."""
        for entity in entities:
            name = entity.get("name", "")
            canonical = self._resolve_canonical(name, alias_map)
            entity["normalizedName"] = canonical
            
            # Add known aliases if not present
            if canonical in self.KNOWN_ALIASES:
                existing_aliases = entity.get("aliases", [])
                for alias in self.KNOWN_ALIASES[canonical]:
                    if alias not in existing_aliases and alias != name.lower():
                        existing_aliases.append(alias)
                entity["aliases"] = existing_aliases
        
        return entities

    def _normalize_cultural_context(self, entities: list) -> list:
        """Normalize cultural context fields."""
        for entity in entities:
            context = entity.get("culturalContext", {})
            if context:
                # Standardize region names
                region = context.get("region", "")
                region_map = {
                    "jawa": "Jawa",
                    "jawa timur": "Jawa Timur",
                    "jawa tengah": "Jawa Tengah",
                    "jawa barat": "Jawa Barat",
                    "kalimantan": "Kalimantan",
                    "kalimantan barat": "Kalimantan Barat",
                    "sumatera": "Sumatera",
                    "sumatera utara": "Sumatera Utara",
                    "sulawesi": "Sulawesi",
                    "bali": "Bali",
                }
                context["region"] = region_map.get(region.lower().strip(), region)
                entity["culturalContext"] = context
        
        return entities

    def _update_claim_entity_refs(self, claims: list, merge_log: list) -> list:
        """Update claim entity references after merging."""
        # Build source-to-target mapping
        id_map = {}
        for merge in merge_log:
            for source_id in merge["sources"]:
                id_map[source_id] = merge["target"]
        
        for claim in claims:
            entity_ids = claim.get("entityIds", [])
            claim["entityIds"] = [id_map.get(eid, eid) for eid in entity_ids]
        
        return claims