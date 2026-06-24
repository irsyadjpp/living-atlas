"""Seed initial taxonomy data for the AI platform.

Run: python -m ai_shared.db.seed
"""

import asyncio
import structlog
from ai_shared.config import ServiceConfig
from ai_shared.database import Database

logger = structlog.get_logger(__name__)

SEED_DATA = """
-- Seed themes
INSERT INTO knowledge.themes (slug, name, description) VALUES
    ('fear', 'Fear', 'Narratives centered around fear, dread, and psychological terror'),
    ('loss', 'Loss', 'Stories about losing loved ones, homes, or cultural heritage'),
    ('afterlife', 'Afterlife', 'Beliefs and encounters related to what exists after death'),
    ('curiosity', 'Curiosity', 'Tales driven by the desire to uncover hidden knowledge'),
    ('forbidden-place', 'Forbidden Place', 'Locations where entry is prohibited due to supernatural danger'),
    ('ancestral-spirits', 'Ancestral Spirits', 'Encounters with spirits of ancestors and lineage guardians'),
    ('supernatural-revenge', 'Supernatural Revenge', 'Stories where supernatural forces deliver vengeance'),
    ('guardian-spirits', 'Guardian Spirits', 'Benevolent spirits that protect people or places'),
    ('warning', 'Warning', 'Narratives that serve as cautionary tales'),
    ('investigation', 'Investigation', 'Structured inquiry into mysterious phenomena'),
    ('witness-testimony', 'Witness Testimony', 'First-hand accounts of supernatural experiences'),
    ('transformation', 'Transformation', 'Stories involving shape-shifting or metamorphosis'),
    ('cultural-identity', 'Cultural Identity', 'Exploration of how folklore shapes community identity')
ON CONFLICT (slug) DO NOTHING;

-- Seed motifs
INSERT INTO knowledge.motifs (slug, name, description) VALUES
    ('mysterious-voice', 'Mysterious Voice', 'Unexplained sounds or voices with no visible source'),
    ('shadow-figure', 'Shadow Figure', 'Dark silhouette or shadowy humanoid form'),
    ('abandoned-house', 'Abandoned House', 'Deserted buildings that harbor supernatural activity'),
    ('sacred-tree', 'Sacred Tree', 'Trees believed to be inhabited by spirits or deities'),
    ('possession', 'Possession', 'Supernatural entities taking control of a person'),
    ('missing-person', 'Missing Person', 'Individuals who vanish under mysterious circumstances'),
    ('ritual-failure', 'Ritual Failure', 'When protective or summoning rituals go wrong'),
    ('dream-vision', 'Dream Vision', 'Prophetic or supernatural messages delivered through dreams'),
    ('guardian-animal', 'Guardian Animal', 'Animals that protect or warn against supernatural threats'),
    ('forbidden-room', 'Forbidden Room', 'A room or space that must not be entered'),
    ('cursed-object', 'Cursed Object', 'Items carrying supernatural curses or attachments'),
    ('time-loop', 'Time Loop', 'Repeating temporal events with supernatural cause'),
    ('doppelganger', 'Doppelganger', 'Supernatural doubles or lookalikes of living persons')
ON CONFLICT (slug) DO NOTHING;

-- Seed archetypes
INSERT INTO knowledge.archetypes (slug, name, description) VALUES
    ('the-skeptic', 'The Skeptic', 'A character who doubts supernatural claims until confronted with evidence'),
    ('the-believer', 'The Believer', 'A character who readily accepts supernatural explanations'),
    ('the-elder', 'The Elder', 'An older figure who holds traditional knowledge and warnings'),
    ('the-shaman', 'The Shaman', 'A spiritual intermediary between the human and spirit worlds'),
    ('the-victim', 'The Victim', 'A character who suffers due to supernatural encounters'),
    ('the-investigator', 'The Investigator', 'A character who systematically researches mysteries'),
    ('the-witness', 'The Witness', 'A character who observed supernatural events firsthand'),
    ('the-guide', 'The Guide', 'A character who helps others navigate supernatural situations'),
    ('the-trickster', 'The Trickster', 'A mischievous supernatural entity that plays tricks on humans'),
    ('the-guardian', 'The Guardian', 'A protective entity or person who guards sacred spaces')
ON CONFLICT (slug) DO NOTHING;

-- Seed narrative patterns
INSERT INTO knowledge.narrative_patterns (slug, name, description) VALUES
    ('warning-ignored', 'Warning Ignored', 'Character receives supernatural warning but proceeds anyway'),
    ('investigation-unfolds', 'Investigation Unfolds', 'Gradual discovery of supernatural truth through inquiry'),
    ('encounter-sequence', 'Encounter Sequence', 'Series of escalating supernatural encounters'),
    ('ritual-gone-wrong', 'Ritual Gone Wrong', 'A ritual or ceremony that produces unexpected results'),
    ('curiosity-leads-to-consequence', 'Curiosity Leads to Consequence', 'Exploring forbidden knowledge leads to supernatural repercussions'),
    ('generational-curse', 'Generational Curse', 'Supernatural affliction passed through family lines'),
    ('rescue-mission', 'Rescue Mission', 'Attempt to save someone from supernatural forces'),
    ('origin-revelation', 'Origin Revelation', 'Discovery of how a supernatural phenomenon began')
ON CONFLICT (slug) DO NOTHING;

-- Seed Indonesia regions
INSERT INTO culture.cultures (name, slug, description) VALUES
    ('Indonesian', 'indonesian', 'The diverse cultures of the Indonesian archipelago'),
    ('Javanese', 'javanese', 'The cultural traditions of Java'),
    ('Sundanese', 'sundanese', 'The cultural traditions of West Java'),
    ('Balinese', 'balinese', 'The cultural traditions of Bali'),
    ('Batak', 'batak', 'The cultural traditions of North Sumatra'),
    ('Minangkabau', 'minangkabau', 'The cultural traditions of West Sumatra'),
    ('Dayak', 'dayak', 'The indigenous cultures of Kalimantan'),
    ('Bugis', 'bugis', 'The cultural traditions of South Sulawesi'),
    ('Toraja', 'toraja', 'The cultural traditions of Tana Toraja'),
    ('Malay', 'malay', 'The Malay cultural traditions across Sumatra and Borneo')
ON CONFLICT (slug) DO NOTHING;

-- Seed Indonesia regions
INSERT INTO culture.regions (name, region_type, country_code) VALUES
    ('Jakarta', 'province', 'ID'),
    ('West Java', 'province', 'ID'),
    ('Central Java', 'province', 'ID'),
    ('East Java', 'province', 'ID'),
    ('Bali', 'province', 'ID'),
    ('North Sumatra', 'province', 'ID'),
    ('West Sumatra', 'province', 'ID'),
    ('South Sulawesi', 'province', 'ID'),
    ('North Sulawesi', 'province', 'ID'),
    ('South Kalimantan', 'province', 'ID'),
    ('East Kalimantan', 'province', 'ID'),
    ('West Kalimantan', 'province', 'ID'),
    ('Central Kalimantan', 'province', 'ID'),
    ('Papua', 'province', 'ID'),
    ('West Nusa Tenggara', 'province', 'ID'),
    ('East Nusa Tenggara', 'province', 'ID'),
    ('Maluku', 'province', 'ID'),
    ('Yogyakarta', 'special_region', 'ID'),
    ('Aceh', 'province', 'ID'),
    ('Riau', 'province', 'ID')
ON CONFLICT DO NOTHING;
"""


async def run_seed():
    """Execute seed data."""
    config = ServiceConfig()
    db = Database(config)
    await db.connect()

    logger.info("seed_started")

    try:
        statements = [s.strip() for s in SEED_DATA.split(";") if s.strip()]
        for i, stmt in enumerate(statements, 1):
            try:
                await db.execute(stmt + ";")
            except Exception as e:
                logger.warning("seed_statement_warning", index=i, error=str(e))

        logger.info("seed_completed", total_statements=len(statements))
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(run_seed())