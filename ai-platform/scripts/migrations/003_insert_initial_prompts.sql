
-- ============================================================
-- Initial Prompt Versions for Enrichment Service
-- PRD v2.0 Compliance
-- ============================================================

-- Theme Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'theme_extraction',
    '1.0.0',
    'theme_extraction',
    'You are analyzing a transcript from Indonesian mystery folklore content.

Your task is to extract themes present in the following transcript segment.

Themes are broad narrative categories such as:
- Fear, Loss, Afterlife, Curiosity, Forbidden Place
- Ancestral Spirits, Supernatural Revenge, Guardian Spirits
- Transformation, Warning, Investigation, Witness Testimony
- Cultural Identity, Colonial Legacy, Modern vs Traditional',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "themes": [
    {
      "name": "string (theme name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript that supports this theme)"
    }
  ]
}

Extract between 1-4 themes. Be conservative — only extract themes with clear evidence.',
    true,
    'Initial theme extraction prompt based on PRD v2.0'
);

-- Motif Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'motif_extraction',
    '1.0.0',
    'motif_extraction',
    'Extract narrative motifs from this Indonesian folklore transcript segment.

Motifs are recurring narrative elements such as:
- Mysterious Voice, Shadow Figure, Abandoned House
- Sacred Tree, Possession, Missing Person
- Ritual Failure, Dream Vision, Guardian Animal
- Transformation, Invisibility, Time Loop',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "motifs": [
    {
      "name": "string (motif name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript that supports this motif)"
    }
  ]
}',
    true,
    'Initial motif extraction prompt based on PRD v2.0'
);

-- Entity Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'entity_extraction',
    '1.0.0',
    'entity_extraction',
    'Extract supernatural entities and named entities from this Indonesian folklore transcript.

Entities include:
- People: witnesses, narrators, community members, cultural authorities
- Spirits: kuntilanak, pocong, genderuwo, sundel bolong
- Creatures: tuyul, leak, other mythological beings
- Locations: villages, forests, rivers, mountains, sacred places
- Objects: ritual items, cursed objects, cultural artifacts',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "entities": [
    {
      "name": "string (entity name)",
      "type": "string (person|spirit|creature|location|object|organization)",
      "description": "string",
      "role_in_story": "string",
      "confidence": float (0.0-1.0)"
    }
  ]
}',
    true,
    'Initial entity extraction prompt based on PRD v2.0'
);

-- Claim Extraction Prompt v1.0.0
INSERT INTO ai.prompt_versions 
(prompt_name, version, task_type, system_prompt, user_prompt_template, is_active, notes)
VALUES (
    'claim_extraction',
    '1.0.0',
    'claim_extraction',
    'Extract claims, assertions, and statements from this Indonesian folklore transcript.

Distinguish between:
- Direct observations (what someone saw/heard)
- Testimony (what someone said they experienced)
- Cultural beliefs (what is believed but not directly observed)
- Interpretations (explanations or theories)
- Hearsay (secondhand information)',
    'TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "claims": [
    {
      "claim": "string (the statement)",
      "claimant": "string (who made the claim)",
      "type": "string (observation|testimony|belief|interpretation|hearsay)",
      "confidence": float (0.0-1.0)",
      "evidence": "string (supporting quote from transcript)",
      "status": "string (verified|unverified|contradicted|cultural_belief)"
    }
  ]
}',
    true,
    'Initial claim extraction prompt based on PRD v2.0'
);
