# ADR-005: Domain-Driven Design Modular Structure

## Status
Accepted

## Context
Traditional Spring Boot applications follow controller → service → repository → entity layering at the application level. This leads to God services, circular dependencies, and poor domain encapsulation. For a knowledge platform with complex domain logic (folklore, culture, provenance), we need stronger domain boundaries.

## Decision
Each service will be structured using Domain-Driven Design with vertical module slicing per bounded context, NOT horizontal layering.

## Rationale
- **Domain complexity**: Knowledge domain requires rich domain models (claims, contradictions, evidence, provenance)
- **Extractability**: Each module is a candidate microservice
- **Team scalability**: Multiple developers can work on separate modules without merge conflicts
- **Ubiquitous language**: Module names match business terminology (story, claim, folklore, belief)

## Consequences
### Positive
- Strong encapsulation prevents cross-module coupling
- Domain logic lives in domain layer, not leaked to services
- Modules can be extracted to microservices independently
- Testing is simpler (domain layer has no infrastructure dependencies)

### Negative
- More boilerplate (interfaces, ports, adapters)
- Requires team discipline to prevent cross-module shortcuts
- Learning curve for DDD newcomers

## Module Communication Rules
1. Modules communicate ONLY through Application layer interfaces
2. Domain layer has ZERO infrastructure dependencies
3. No cross-module database access
4. No shared JPA entities across modules
5. Domain events are the only allowed cross-module contract

## Package Convention
```
com.livingatlas.{service}.{module}
Example: com.livingatlas.knowledge.claims

{module}/
├── api/              # REST controllers, request/response DTOs
│   └── dto/
├── application/      # Use case services, application DTOs, ports
│   └── port/
├── domain/           # Entities, value objects, domain events, repository interfaces
│   ├── event/
│   ├── model/
│   └── repository/
├── infrastructure/   # JPA repositories, message producers, REST clients
│   ├── persistence/
│   └── messaging/
└── projection/       # Graph/vector sync event handlers
```

## References
- plan.md - Spring Boot Internal Structure
- BACKEND-PRD.md §9 Internal Service Structure