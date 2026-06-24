"""Neo4j Knowledge Graph Sync Service.

Syncs validated canonical stories from PostgreSQL to Neo4j knowledge graph.
Creates entities, relationships, and maintains the cultural knowledge graph.
"""

import json
import uuid
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass

import structlog
from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession

from ai_shared.config import ServiceConfig
from ai_shared.database import Database
from ai_shared.canonical import CanonicalStory

logger = structlog.get_logger(__name__)


@dataclass
class Neo4jConfig:
    """Neo4j connection configuration."""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"


class Neo4jGraphSyncService:
    """Service to sync validated canonical stories to Neo4j knowledge graph.
    
    Graph Schema:
    - Node types: Entity, Story, Location, Belief, Ritual, Tradition
    - Relationship types: APPEARS_IN, RELATES_TO, LOCATED_AT, INFLUENCED_BY, etc.
    - Properties: maintain source tracking and metadata
    """

    def __init__(
        self,
        neo4j_config: Neo4jConfig,
        postgres_db: Database,
    ):
        self.neo4j_config = neo4j_config
        self.postgres_db = postgres_db
        self.driver: Optional[AsyncDriver] = None

    async def start(self):
        """Initialize Neo4j driver connection."""
        logger.info(
            "neo4j_sync_service_starting",
            uri=self.neo4j_config.uri,
            database=self.neo4j_config.database,
        )
        
        self.driver = AsyncGraphDatabase.driver(
            self.neo4j_config.uri,
            auth=(self.neo4j_config.username, self.neo4j_config.password),
        )
        
        # Test connection
        await self._test_connection()
        
        # Create constraints and indexes
        await self._setup_graph_schema()
        
        logger.info("neo4j_sync_service_started")

    async def stop(self):
        """Close Neo4j driver connection."""
        if self.driver:
            await self.driver.close()
            logger.info("neo4j_sync_service_stopped")

    async def _test_connection(self):
        """Test Neo4j connection."""
        try:
            async with self.driver.session(database=self.neo4j_config.database) as session:
                result = await session.run("RETURN 1 AS test")
                await result.consume()
            logger.info("neo4j_connection_test_succeeded")
        except Exception as e:
            logger.error("neo4j_connection_test_failed", error=str(e))
            raise

    async def _setup_graph_schema(self):
        """Create graph constraints and indexes."""
        async with self.driver.session(database=self.neo4j_config.database) as session:
            # Create uniqueness constraints
            constraints = [
                "CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
                "CREATE CONSTRAINT story_id_unique IF NOT EXISTS FOR (s:Story) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
                "CREATE CONSTRAINT belief_id_unique IF NOT EXISTS FOR (b:Belief) REQUIRE b.id IS UNIQUE",
                "CREATE CONSTRAINT ritual_id_unique IF NOT EXISTS FOR (r:Ritual) REQUIRE r.id IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.warning("constraint_creation_failed", constraint=constraint, error=str(e))
            
            # Create indexes
            indexes = [
                "CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)",
                "CREATE INDEX story_title_index IF NOT EXISTS FOR (s:Story) ON (s.title)",
                "CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.entity_type)",
            ]
            
            for index in indexes:
                try:
                    await session.run(index)
                except Exception as e:
                    logger.warning("index_creation_failed", index=index, error=str(e))

    async def sync_canonical_story(self, canonical_story_id: str) -> dict:
        """Sync a validated canonical story to Neo4j knowledge graph.
        
        Args:
            canonical_story_id: UUID of the canonical story
            
        Returns:
            Sync statistics (nodes created, relationships created)
        """
        logger.info("sync_canonical_story_started", canonical_story_id=canonical_story_id)
        
        # Retrieve canonical story from PostgreSQL
        canonical_story = await self._get_canonical_story(canonical_story_id)
        
        if not canonical_story:
            logger.error("canonical_story_not_found", canonical_story_id=canonical_story_id)
            return {"error": "Canonical story not found"}
        
        stats = {"nodes_created": 0, "relationships_created": 0}
        
        # Sync in a transaction
        async with self.driver.session(database=self.neo4j_config.database) as session:
            async with session.begin_transaction() as tx:
                # Create Story node
                story_node_id = await self._create_story_node(tx, canonical_story, canonical_story_id)
                stats["nodes_created"] += 1
                
                # Create Entity nodes and relationships
                for entity in canonical_story.entities:
                    entity_node_id = await self._create_entity_node(tx, entity)
                    stats["nodes_created"] += 1
                    
                    # Create APPEARS_IN relationship
                    await tx.run(
                        """
                        MATCH (e:Entity {id: $entity_id})
                        MATCH (s:Story {id: $story_id})
                        MERGE (e)-[r:APPEARS_IN]->(s)
                        SET r.role_in_story = $role, r.confidence = $confidence
                        """,
                        entity_id=entity_node_id,
                        story_id=story_node_id,
                        role=entity.role_in_story,
                        confidence=entity.confidence,
                    )
                    stats["relationships_created"] += 1
                
                # Create Location nodes and relationships
                for location in canonical_story.locations:
                    location_node_id = await self._create_location_node(tx, location)
                    stats["nodes_created"] += 1
                    
                    await tx.run(
                        """
                        MATCH (l:Location {id: $location_id})
                        MATCH (s:Story {id: $story_id})
                        MERGE (s)-[r:SET_IN]->(l)
                        SET r.confidence = $confidence
                        """,
                        location_id=location_node_id,
                        story_id=story_node_id,
                        confidence=location.confidence,
                    )
                    stats["relationships_created"] += 1
                
                # Create Belief nodes and relationships
                for belief in canonical_story.beliefs:
                    belief_node_id = await self._create_belief_node(tx, belief)
                    stats["nodes_created"] += 1
                    
                    await tx.run(
                        """
                        MATCH (b:Belief {id: $belief_id})
                        MATCH (s:Story {id: $story_id})
                        MERGE (s)-[r:EXPRESSES]->(b)
                        SET r.confidence = $confidence
                        """,
                        belief_id=belief_node_id,
                        story_id=story_node_id,
                        confidence=belief.confidence,
                    )
                    stats["relationships_created"] += 1
                
                # Create Ritual nodes and relationships
                for ritual in canonical_story.rituals:
                    ritual_node_id = await self._create_ritual_node(tx, ritual)
                    stats["nodes_created"] += 1
                    
                    await tx.run(
                        """
                        MATCH (r:Ritual {id: $ritual_id})
                        MATCH (s:Story {id: $story_id})
                        MERGE (s)-[r2:DESCRIBES]->(r)
                        SET r2.confidence = $confidence
                        """,
                        ritual_id=ritual_node_id,
                        story_id=story_node_id,
                        confidence=ritual.confidence,
                    )
                    stats["relationships_created"] += 1
                
                # Create Claim nodes and relationships
                for claim in canonical_story.claims:
                    claim_node_id = await self._create_claim_node(tx, claim)
                    stats["nodes_created"] += 1
                    
                    await tx.run(
                        """
                        MATCH (c:Claim {id: $claim_id})
                        MATCH (s:Story {id: $story_id})
                        MERGE (s)-[r:CONTAINS_CLAIM]->(c)
                        SET r.claim_type = $claim_type, r.veracity = $veracity
                        """,
                        claim_id=claim_node_id,
                        story_id=story_node_id,
                        claim_type=claim.claim_type.value,
                        veracity=claim.veracity,
                    )
                    stats["relationships_created"] += 1
                
                # Create relationships between entities based on canonical_story.entity_relationships
                for rel in canonical_story.entity_relationships:
                    await tx.run(
                        """
                        MATCH (e1:Entity {name: $source_entity})
                        MATCH (e2:Entity {name: $target_entity})
                        MERGE (e1)-[r:RELATES_TO]->(e2)
                        SET r.relationship_type = $rel_type, r.confidence = $confidence
                        """,
                        source_entity=rel.source_entity,
                        target_entity=rel.target_entity,
                        rel_type=rel.relationship_type,
                        confidence=rel.confidence,
                    )
                    stats["relationships_created"] += 1
                
                # Mark story as synced in PostgreSQL
                await self._mark_story_as_synced(canonical_story_id)
                
                await tx.commit()
        
        logger.info(
            "sync_canonical_story_completed",
            canonical_story_id=canonical_story_id,
            stats=stats,
        )
        
        return stats

    async def _get_canonical_story(self, canonical_story_id: str) -> Optional[CanonicalStory]:
        """Retrieve canonical story from PostgreSQL."""
        result = await self.postgres_db.fetchrow(
            "SELECT canonical_data FROM canonical.stories WHERE id = $1 AND is_validated = true",
            canonical_story_id,
        )
        
        if result:
            canonical_data = json.loads(result["canonical_data"])
            return CanonicalStory(**canonical_data)
        return None

    async def _create_story_node(self, tx, canonical_story: CanonicalStory, canonical_story_id: str) -> str:
        """Create or update Story node in Neo4j."""
        node_id = f"story_{canonical_story_id}"
        
        await tx.run(
            """
            MERGE (s:Story {id: $node_id})
            SET s.title = $title,
                s.summary = $summary,
                s.story_type = $story_type,
                s.primary_culture = $primary_culture,
                s.region = $region,
                s.time_period = $time_period,
                s.confidence = $confidence,
                s.source_video_id = $source_video_id,
                s.created_at = $created_at
            """,
            node_id=node_id,
            title=canonical_story.story.title,
            summary=canonical_story.story.summary,
            story_type=canonical_story.story.story_type.value,
            primary_culture=canonical_story.story.primary_culture,
            region=canonical_story.story.region,
            time_period=canonical_story.story.time_period,
            confidence=canonical_story.story.confidence,
            source_video_id=canonical_story.source_video_id,
            created_at=canonical_story.extraction_date.isoformat() if canonical_story.extraction_date else datetime.utcnow().isoformat(),
        )
        
        return node_id

    async def _create_entity_node(self, tx, entity) -> str:
        """Create or update Entity node in Neo4j."""
        node_id = f"entity_{entity.name.lower().replace(' ', '_')}"
        
        await tx.run(
            """
            MERGE (e:Entity {id: $node_id})
            SET e.name = $name,
                e.entity_type = $entity_type,
                e.description = $description,
                e.cultural_significance = $cultural_significance,
                e.aliases = $aliases,
                e.confidence = $confidence
            """,
            node_id=node_id,
            name=entity.name,
            entity_type=entity.entity_type.value,
            description=entity.description,
            cultural_significance=entity.cultural_significance,
            aliases=entity.aliases,
            confidence=entity.confidence,
        )
        
        return node_id

    async def _create_location_node(self, tx, location) -> str:
        """Create or update Location node in Neo4j."""
        node_id = f"location_{location.name.lower().replace(' ', '_')}"
        
        await tx.run(
            """
            MERGE (l:Location {id: $node_id})
            SET l.name = $name,
                l.location_type = $location_type,
                l.coordinates = $coordinates,
                l.administrative_region = $admin_region,
                l.confidence = $confidence
            """,
            node_id=node_id,
            name=location.name,
            location_type=location.location_type.value,
            coordinates=json.dumps(location.coordinates) if location.coordinates else None,
            admin_region=location.administrative_region,
            confidence=location.confidence,
        )
        
        return node_id

    async def _create_belief_node(self, tx, belief) -> str:
        """Create or update Belief node in Neo4j."""
        node_id = f"belief_{belief.name.lower().replace(' ', '_')}"
        
        await tx.run(
            """
            MERGE (b:Belief {id: $node_id})
            SET b.name = $name,
                b.description = $description,
                b.belief_type = $belief_type,
                b.practice_count = $practice_count,
                b.confidence = $confidence
            """,
            node_id=node_id,
            name=belief.name,
            description=belief.description,
            belief_type=belief.belief_type.value,
            practice_count=belief.practice_count,
            confidence=belief.confidence,
        )
        
        return node_id

    async def _create_ritual_node(self, tx, ritual) -> str:
        """Create or update Ritual node in Neo4j."""
        node_id = f"ritual_{ritual.name.lower().replace(' ', '_')}"
        
        await tx.run(
            """
            MERGE (r:Ritual {id: $node_id})
            SET r.name = $name,
                r.description = $description,
                r.ritual_type = $ritual_type,
                r.occasions = $occasions,
                r.confidence = $confidence
            """,
            node_id=node_id,
            name=ritual.name,
            description=ritual.description,
            ritual_type=ritual.ritual_type.value,
            occasions=json.dumps(ritual.occasions),
            confidence=ritual.confidence,
        )
        
        return node_id

    async def _create_claim_node(self, tx, claim) -> str:
        """Create or update Claim node in Neo4j."""
        node_id = f"claim_{uuid.uuid4().hex[:8]}"
        
        await tx.run(
            """
            MERGE (c:Claim {id: $node_id})
            SET c.content = $content,
                c.claim_type = $claim_type,
                c.veracity = $veracity,
                c.confidence = $confidence,
                c.source_evidence = $source_evidence
            """,
            node_id=node_id,
            content=claim.content,
            claim_type=claim.claim_type.value,
            veracity=claim.veracity,
            confidence=claim.confidence,
            source_evidence=json.dumps(claim.source_evidence),
        )
        
        return node_id

    async def _mark_story_as_synced(self, canonical_story_id: str):
        """Mark story as synced to Neo4j in PostgreSQL."""
        await self.postgres_db.execute(
            "UPDATE canonical.stories SET synced_to_graph = true, synced_at = now() WHERE id = $1",
            canonical_story_id,
        )