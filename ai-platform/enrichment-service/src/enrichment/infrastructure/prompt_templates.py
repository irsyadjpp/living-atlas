"""Jinja2 prompt templates for LLM extraction.

Each template defines the structured extraction prompt for a specific
knowledge domain: themes, motifs, archetypes, entities, claims, relationships, stories.
All prompts are versioned for tracking and rollback.
"""

from jinja2 import Template


THEME_EXTRACTION_TEMPLATE = Template("""
You are analyzing a transcript from Indonesian mystery folklore content.

Your task is to extract themes present in the following transcript segment.

Themes are broad narrative categories such as:
- Fear, Loss, Afterlife, Curiosity, Forbidden Place
- Ancestral Spirits, Supernatural Revenge, Guardian Spirits
- Transformation, Warning, Investigation, Witness Testimony
- Cultural Identity, Colonial Legacy, Modern vs Traditional

TRANSCRIPT SEGMENT:
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

Extract between 1-4 themes. Be conservative — only extract themes with clear evidence.
""")


MOTIF_EXTRACTION_TEMPLATE = Template("""
Extract narrative motifs from this Indonesian folklore transcript segment.

Motifs are recurring narrative elements such as:
- Mysterious Voice, Shadow Figure, Abandoned House
- Sacred Tree, Possession, Missing Person
- Ritual Failure, Dream Vision, Guardian Animal
- Transformation, Invisibility, Time Loop

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "motifs": [
    {
      "name": "string (motif name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript)"
    }
  ]
}

Extract between 1-4 motifs.
""")


ARCHETYPE_EXTRACTION_TEMPLATE = Template("""
Extract archetypes from this Indonesian folklore transcript segment.

Archetypes are universal character patterns such as:
- The Skeptic, The Believer, The Elder, The Shaman
- The Victim, The Investigator, The Witness
- The Guide, The Trickster, The Guardian

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "archetypes": [
    {
      "name": "string (archetype name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (quote from transcript)"
    }
  ]
}

Extract between 0-3 archetypes.
""")


ENTITY_EXTRACTION_TEMPLATE = Template("""
Extract supernatural entities, folklore beings, and important named entities
from this Indonesian mystery folklore transcript.

Entity types include: spirit, ghost, entity, person, character, location,
ritual, belief, tradition, creature, mythological_being

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "entities": [
    {
      "name": "string (entity name)",
      "type": "string (entity type from list above)",
      "aliases": ["string (alternative names, if any)"],
      "description": "string (brief description)",
      "confidence": float (0.0-1.0)
    }
  ]
}

Extract between 0-5 entities.
""")


CLAIM_EXTRACTION_TEMPLATE = Template("""
Extract factual claims from this Indonesian folklore transcript segment.

Claims are statements that assert something about:
- Origins of supernatural beings
- Locations where events occurred
- Rituals or practices described
- Beliefs held by the community
- Relationships between entities

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "claims": [
    {
      "text": "string (the exact claim)",
      "claim_type": "string (origin|location|ritual|belief|relationship)",
      "confidence": float (0.0-1.0),
      "evidence": "string (supporting quote from transcript)"
    }
  ]
}

Extract between 0-5 claims.
""")


RELATIONSHIP_EXTRACTION_TEMPLATE = Template("""
Extract relationships between entities mentioned in this Indonesian folklore transcript.

Relationships describe how entities are connected, for example:
- (Kuntilanak) -[ASSOCIATED_WITH]-> (Kalimantan)
- (Ratu Kidul) -[RULES]-> (Southern Sea)
- (Joko Tarub) -[MARRIED]-> (Nawang Wulan)

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "relationships": [
    {
      "subject": "string (entity name)",
      "predicate": "string (relationship type in UPPER_CASE)",
      "object": "string (related entity name)",
      "confidence": float (0.0-1.0),
      "evidence": "string (supporting quote)"
    }
  ]
}

Extract between 0-5 relationships.
""")


STORY_BOUNDARY_TEMPLATE = Template("""
Analyze this Indonesian folklore transcript and identify distinct stories within it.

A single video may contain multiple separate stories or accounts.
Identify where each story begins and ends.

TRANSCRIPT SEGMENT:
{{ transcript_text }}

Respond with a JSON object:
{
  "stories": [
    {
      "title": "string (descriptive title for the story)",
      "start_timestamp": float (start time in seconds, 0 if unknown),
      "end_timestamp": float (end time in seconds, 0 if unknown),
      "summary": "string (brief 1-2 sentence summary)",
      "confidence": float (0.0-1.0)
    }
  ]
}

Extract between 0-5 stories. If the entire transcript is one story, return a single entry.
""")


# Registry of all prompt templates with their default versions
PROMPT_REGISTRY = {
    "theme": {"template": THEME_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "motif": {"template": MOTIF_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "archetype": {"template": ARCHETYPE_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "entity": {"template": ENTITY_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "claim": {"template": CLAIM_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "relationship": {"template": RELATIONSHIP_EXTRACTION_TEMPLATE, "version": "1.0.0"},
    "story_boundary": {"template": STORY_BOUNDARY_TEMPLATE, "version": "1.0.0"},
}