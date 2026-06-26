# ADR-002: Modular Monolith First

## Status
Accepted

## Context
We need to choose between microservices and monolith for initial architecture. Microservices add operational complexity (network latency, distributed transactions, service mesh, observability overhead) that is unjustified at current scale (100–5000 users). However, we must not paint ourselves into a corner where extraction to microservices becomes impossible.

## Decision
We will implement a modular monolith architecture where each service is internally structured as independent bounded context modules, deployed as a single unit but designed for future extraction into separate services.

## Rationale
- **Current scale**: 100–5000 users does not justify microservice overhead
- **Team size**: Small team cannot maintain 10+ services operationally
- **Development velocity**: Faster iteration without service boundary ceremony
- **Extraction-ready**: DDD module boundaries prepare clean extraction paths

## Consequences
### Positive
- Single deployment unit reduces DevOps complexity
- Local development is straightforward
- Shared in-memory caching and transactions
- Easier debugging and testing

### Negative
- Requires strong discipline to maintain module boundaries
- No independent scaling per module
- Single point of deployment risk

## Module Structure (per service)
```
knowledge-service/
├── knowledge/
│   ├── api/              # REST controllers
│   ├── application/      # Use cases, DTOs
│   ├── domain/           # Entities, value objects, domain events
│   ├── infrastructure/   # Repositories, DB adapters
│   └── projection/       # Graph/vector sync triggers
├── claims/
│   ├── api/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   └── projection/
└── folklore/
    ├── api/
    ├── application/
    ├── domain/
    ├── infrastructure/
    └── projection/
```

## Extraction Trigger Conditions
1. Team grows beyond 5 engineers per module
2. Module requires independent scaling (CPU/memory profile divergence)
3. Module requires independent deployment cycle
4. Clear evidence of deployment conflicts between modules

## References
- plan.md - Spring Boot Internal Structure
- BACKEND-PRD.md §2.2 Modular Monolith First