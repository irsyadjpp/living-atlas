# ADR-006: Service Boundaries and Ownership

## Status
Accepted

## Context
The platform has multiple services (gateway, identity, content, knowledge, research, workflow). Clear service boundaries prevent ownership disputes, circular dependencies, and data duplication.

## Decision
Service boundaries are defined by domain ownership, not technical layers. Each service owns its data and domain logic exclusively.

## Rationale
- **Domain isolation**: Each service owns a complete business capability
- **Data ownership**: No shared databases between services
- **Independent deployability**: Services can evolve independently
- **Team alignment**: Service boundaries map to team responsibilities

## Service Boundaries

| Service | Domain | Owns | Does Not Own |
|---------|--------|------|--------------|
| gateway-service | API Gateway | Routing, auth delegation, rate limiting | Business logic, data |
| identity-service | Identity & Access | Users, tenants, roles, policies, workspaces | Content, knowledge |
| content-service | Content | Stories, articles, sources, transcripts, evidence | Users, knowledge graph |
| knowledge-service | Knowledge | Knowledge objects, themes, motifs, claims, contradictions | Content, users |
| research-service | Research | Collections, annotations, notes, saved queries | Content, knowledge |
| workflow-service | Workflow | Reviews, approvals, publishing state machines | Content, knowledge |

## Communication Patterns
1. **Synchronous (REST)**: Query operations, command operations requiring immediate response
2. **Asynchronous (Events)**: State changes that trigger downstream processing
3. **Forbidden**: Direct database access to another service's schema
4. **Forbidden**: Shared JPA entities across services

## Cross-Service Data Flow
```
identity-service → gateway-service: JWT token with claims
content-service → knowledge-service: StoryCreated event
knowledge-service → content-service: KnowledgeObjectLinked event
content-service → workflow-service: StorySubmittedForReview event
workflow-service → content-service: StoryApproved event
```

## References
- plan.md - Services
- BACKEND-PRD.md §3 Functional Domains