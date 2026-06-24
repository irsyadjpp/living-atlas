"""Story Canonicalization Orchestrator - Core Knowledge Extraction.

This is the MOST IMPORTANT component in the entire system.
Transforms raw, messy transcripts into structured canonical cultural knowledge.

All articles, knowledge graphs, and future AI systems depend on this output.
"""

from dataclasses import dataclass
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID


class StoryType(str, Enum):
    """Types of stories in the corpus."""
    DOCUMENTARY = "documentary"
    WITNESS_TESTIMONY = "witness_testimony"
    CREATOR_EXPLORATION = "creator_exploration"
    FOLKLORE_DOCUMENTATION = "folklore_documentation"
    CEREMONIAL_RECORDING = "ceremonial_recording"
    HISTORICAL_ACCOUNT = "historical_account"
    MYTHOLOGICAL_RETELLING = "mythological_retelling"
    INVESTIGATIVE_JOURNALISM = "investigative_journalism"


class EntityType(str, Enum):
    """Types of entities in the knowledge graph."""
    PERSON = "person"
    SPIRIT = "spirit"
    CREATURE = "creature"
    LOCATION = "location"
    STRUCTURE = "structure"
    OBJECT = "object"
    RITUAL = "ritual"
    TRADITION = "tradition"
    ORGANIZATION = "organization"
    CONCEPT = "concept"


class LocationType(str, Enum):
    """Types of locations."""
    VILLAGE = "village"
    FOREST = "forest"
    MOUNTAIN = "mountain"
    RIVER = "river"
    LAKE = "lake"
    SEA = "sea"
    TEMPLE = "temple"
    SHRINE = "shrine"
    CEMETERY = "cemetery"
    CAVE = "cave"
    HOUSE = "house"
    PALACE = "palace"
    RUINS = "ruins"
    ROAD = "road"
    REGION = "region"
    UNKNOWN = "unknown"


class ClaimType(str, Enum):
    """Types of claims extracted from testimony."""
    OBSERVATION = "observation"
    TESTIMONY = "testimony"
    CULTURAL_BELIEF = "cultural_belief"
    INTERPRETATION = "interpretation"
    HEARSAY = "hearsay"
    CREATOR_COMMENTARY = "creator_commentary"
    HISTORICAL_FACT = "historical_fact"


class EvidenceSource(BaseModel):
    """Source of evidence for a claim."""
    source_type: str = Field(..., description="transcript | video | interview | document")
    timestamp_or_position: Optional[str] = Field(None, description="Timestamp or position in source")
    credibility_score: float = Field(..., ge=0.0, le=1.0, description="Source credibility")
    quote: Optional[str] = Field(None, description="Direct quote from source")


class Claim(BaseModel):
    """A claim extracted from the source material."""
    claim: str = Field(..., description="The claim statement")
    claim_type: ClaimType = Field(..., description="Type of claim")
    claimant: Optional[str] = Field(None, description="Who made the claim")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in claim veracity")
    evidence: List[EvidenceSource] = Field(default_factory=list, description="Supporting evidence")
    context: Optional[str] = Field(None, description="Contextual information")
    status: str = Field(default="unverified", description="verified | unverified | contradicted | disputed")


class Contradiction(BaseModel):
    """Detected contradictions between sources."""
    claim_a: str = Field(..., description="First conflicting claim")
    claim_b: str = Field(..., description="Second conflicting claim")
    source_a: str = Field(..., description="Source of first claim")
    source_b: str = Field(..., description="Source of second claim")
    nature: str = Field(..., description="direct contradiction | nuance difference | context dependent")
    resolution: Optional[str] = Field(None, description="How or if contradiction can be resolved")


class Entity(BaseModel):
    """An entity in the story (person, spirit, location, etc.)."""
    name: str = Field(..., description="Canonical name")
    aliases: List[str] = Field(default_factory=list, description="Alternative names/spellings")
    entity_type: EntityType = Field(..., description="Type of entity")
    description: str = Field(..., description="Description of entity")
    role_in_story: str = Field(..., description="Role in this specific story")
    cultural_significance: Optional[str] = Field(None, description="Broader cultural significance")
    confidence: float = Field(..., ge=0.0, le=1.0)
    first_mention_position: Optional[str] = Field(None, description="Where entity first appears")


class Location(BaseModel):
    """A geographical location in the story."""
    name: str = Field(..., description="Canonical location name")
    location_type: LocationType = Field(..., description="Type of location")
    is_sensitive: bool = Field(default=False, description="Location is culturally sensitive")
    public_region: str = Field(..., description="Publicly known region (e.g., Yogyakarta)")
    description: str = Field(..., description="Description of location")
    significance_in_story: str = Field(..., description="Role in this story")
    cultural_context: Optional[str] = Field(None, description="Cultural significance")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Belief(BaseModel):
    """A cultural or supernatural belief."""
    belief: str = Field(..., description="The belief statement")
    culture: str = Field(..., description="Which culture holds this belief")
    community: Optional[str] = Field(None, description="Specific community or subgroup")
    practice: Optional[str] = Field(None, description="If belief leads to practice")
    evidence: List[str] = Field(default_factory=list, description="Supporting quotes")
    variations: List[str] = Field(default_factory=list, description="Variations of this belief")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Ritual(BaseModel):
    """A ritual or ceremonial practice."""
    name: str = Field(..., description="Name of ritual")
    purpose: str = Field(..., description="Purpose of the ritual")
    culture: str = Field(..., description="Which culture")
    steps: List[str] = Field(default_factory=list, description="Steps or sequence")
    requirements: List[str] = Field(default_factory=list, description="What is needed")
    taboos: List[str] = Field(default_factory=list, description="What is forbidden")
    timing: Optional[str] = Field(None, description="When it is performed")
    description: str = Field(..., description="Full description")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Tradition(BaseModel):
    """A cultural tradition."""
    name: str = Field(..., description="Name of tradition")
    culture: str = Field(..., description="Which culture")
    description: str = Field(..., description="Description of tradition")
    practice: List[str] = Field(default_factory=list, description="How it is practiced")
    origin_story: Optional[str] = Field(None, description="Origin if known")
    modern_status: str = Field(..., description="still_practiced | modified | discontinued")
    confidence: float = Field(..., ge=0.0, le=1.0)


class CulturalObject(BaseModel):
    """An object with cultural significance."""
    name: str = Field(..., description="Name of object")
    object_type: str = Field(..., description="tool | artifact | symbol | offering | weapon | etc.")
    purpose: str = Field(..., description="Purpose of object")
    cultural_significance: str = Field(..., description="Why it matters")
    description: str = Field(..., description="Physical description")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Event(BaseModel):
    """An event in the story."""
    event: str = Field(..., description="Description of event")
    event_type: str = Field(..., description="ritual | encounter | observation | conflict | transition")
    participants: List[str] = Field(default_factory=list, description="Who was involved")
    location: Optional[str] = Field(None, description="Where it happened")
    timing: Optional[str] = Field(None, description="When it happened")
    outcome: Optional[str] = Field(None, description="What happened as a result")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Theme(BaseModel):
    """A thematic element in the story."""
    name: str = Field(..., description="Theme name")
    description: str = Field(..., description="What this theme means in context")
    evidence: List[str] = Field(default_factory=list, description="Supporting quotes")
    confidence: float = Field(..., ge=0.0, le=1.0)


class Motif(BaseModel):
    """A recurring narrative motif."""
    name: str = Field(..., description="Motif name")
    description: str = Field(..., description="What this motif represents")
    occurrences: List[str] = Field(default_factory=list, description="Where it appears in story")
    variations: List[str] = Field(default_factory=list, description="Different forms it takes")
    confidence: float = Field(..., ge=0.0, le=1.0)


class NarrativePattern(BaseModel):
    """A narrative structure or pattern."""
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="How the pattern works")
    examples_in_story: List[str] = Field(default_factory=list, description="Where it appears")
    cultural_significance: Optional[str] = Field(None, description="Why this pattern matters")
    confidence: float = Field(..., ge=0.0, le=1.0)


class WitnessTestimony(BaseModel):
    """Direct testimony from a witness."""
    witness_name: str = Field(..., description="Who testified")
    testimony: str = Field(..., description="What they said")
    context: str = Field(..., description="Context of testimony")
    credibility_score: float = Field(..., ge=0.0, le=1.0)
    position_or_timestamp: Optional[str] = Field(None, description="When they said it")


class CreatorObservation(BaseModel):
    """Observations made by the content creator."""
    creator_name: str = Field(..., description="Who made the observation")
    observation: str = Field(..., description="What they observed")
    type_of_observation: str = Field(..., description="direct | analytical | speculative")
    context: str = Field(..., description="Context of observation")


class ResearchGap(BaseModel):
    """Information that is missing or needs further research."""
    gap_description: str = Field(..., description="What is unknown")
    importance: str = Field(..., description="low | medium | high | critical")
    suggested_research: Optional[str] = Field(None, description="How to investigate")
    related_entities: List[str] = Field(default_factory=list, description="Entities involved")


class Uncertainty(BaseModel):
    """Explicitly marked uncertainty in the source."""
    topic: str = Field(..., description="What is uncertain")
    nature_of_uncertainty: str = Field(..., description="ambiguous_source | contradictory_accounts | unknown_origin | etc.")
    source_of_uncertainty: str = Field(..., description="Where the uncertainty comes from")


class ResearchNote(BaseModel):
    """Additional context for future researchers."""
    note: str = Field(..., description="The note")
    relevance: str = Field(..., description="Why this matters")
    category: str = Field(..., description="context | cross_reference | warning | opportunity")


class Story(BaseModel):
    """The canonical story metadata."""
    title: str = Field(..., description="Canonical title of the story")
    summary: str = Field(..., description="2-3 sentence summary")
    story_type: StoryType = Field(..., description="Type of story")
    primary_culture: str = Field(..., description="Primary culture represented")
    region: str = Field(..., description="Geographical region")
    time_period: Optional[str] = Field(None, description="When the story takes place (if applicable)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in story structure")


class CanonicalStory(BaseModel):
    """The complete canonical story output from Story Canonicalization Orchestrator.

    This is the SINGLE SOURCE OF TRUTH for all downstream processing:
    - Knowledge graph construction
    - Article generation (all 4 types)
    - Research and academic use
    - Future AI systems
    """
    
    # Core story information
    story: Story = Field(..., description="Story metadata")
    
    # Entities and locations
    entities: List[Entity] = Field(default_factory=list, description="All entities in the story")
    locations: List[Location] = Field(default_factory=list, description="All locations")
    
    # Cultural elements
    cultures: List[str] = Field(default_factory=list, description="Cultures represented")
    ethnic_groups: List[str] = Field(default_factory=list, description="Ethnic groups mentioned")
    beliefs: List[Belief] = Field(default_factory=list, description="Cultural and supernatural beliefs")
    rituals: List[Ritual] = Field(default_factory=list, description="Rituals and ceremonies")
    traditions: List[Tradition] = Field(default_factory=list, description="Cultural traditions")
    objects: List[CulturalObject] = Field(default_factory=list, description="Objects with cultural significance")
    
    # Narrative elements
    events: List[Event] = Field(default_factory=list, description="Key events in chronological order")
    themes: List[Theme] = Field(default_factory=list, description="Thematic elements")
    motifs: List[Motif] = Field(default_factory=list, description="Recurring narrative motifs")
    narrative_patterns: List[NarrativePattern] = Field(default_factory=list, description="Narrative structures")
    
    # Claims and evidence
    claims: List[Claim] = Field(default_factory=list, description="All claims with evidence")
    contradictions: List[Contradiction] = Field(default_factory=list, description="Detected contradictions")
    witness_testimonies: List[WitnessTestimony] = Field(default_factory=list, description="Direct witness accounts")
    creator_observations: List[CreatorObservation] = Field(default_factory=list, description="Creator's observations")
    
    # Research metadata
    research_gaps: List[ResearchGap] = Field(default_factory=list, description="Missing information")
    uncertainties: List[Uncertainty] = Field(default_factory=list, description="Explicitly marked uncertainties")
    research_notes: List[ResearchNote] = Field(default_factory=list, description="Additional context")
    
    # Source metadata
    source_video_id: Optional[UUID] = Field(None, description="Source video UUID")
    source_transcript_id: Optional[UUID] = Field(None, description="Source transcript UUID")
    extraction_date: Optional[str] = Field(None, description="When this canonical story was extracted")
    extraction_model: str = Field(default="gemini-1.5-flash", description="Model used for extraction")
    extraction_version: str = Field(default="1.0.0", description="Version of extraction schema")
    
    class Config:
        json_schema_extra = {
            "example": {
                "story": {
                    "title": "Malam Satu Suro di Keraton Yogyakarta",
                    "summary": "Pengamatan ritual mubeng beteng pada malam satu suro yang dilakukan oleh komunitas Jawa Yogyakarta sebagai sarana introspeksi diri.",
                    "story_type": "ceremonial_recording",
                    "primary_culture": "Jawa",
                    "region": "Yogyakarta",
                    "confidence": 0.92
                },
                "entities": [
                    {
                        "name": "Kanjeng Raden Tumenggung",
                        "aliases": ["KRT"],
                        "entity_type": "person",
                        "description": "Tokoh budaya Yogyakarta yang menjelaskan tradisi mubeng beteng",
                        "role_in_story": "informant",
                        "confidence": 0.95
                    }
                ],
                "locations": [
                    {
                        "name": "Keraton Yogyakarta",
                        "location_type": "palace",
                        "is_sensitive": False,
                        "public_region": "Yogyakarta",
                        "description": "Pusat budaya Jawa di Yogyakarta",
                        "significance_in_story": "lokasi ritual",
                        "confidence": 0.98
                    }
                ]
            }
        }