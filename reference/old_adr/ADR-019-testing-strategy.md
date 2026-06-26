# ADR-019: Testing Strategy

## Status
Accepted

## Context
The platform has multiple services with complex domain logic (knowledge extraction, state machines, event processing). Without a structured testing strategy, quality will degrade as the codebase grows.

## Decision
We adopt the Test Pyramid with hexagonal architecture testing: unit tests for domain logic, integration tests for infrastructure adapters, contract tests for API boundaries, and end-to-end tests for critical paths.

## Rationale
- **Domain complexity**: Knowledge claims, contradictions, and state machines require thorough unit testing
- **Event-driven complexity**: Outbox processing, event handlers need integration testing
- **Multi-language**: Java services and Python AI services need different testing approaches
- **Quality gates**: CI pipeline enforces test coverage thresholds

## Test Pyramid
```
    ╱╲
   ╱ E2E ╲           ← Few: Critical business paths
  ╱────────╲
 ╱ Contract ╲        ← Some: API contract compliance
╱──────────────╲
╱ Integration     ╲  ← More: Repository, event handler, adapter tests
╱────────────────────╲
╱    Unit Tests        ╲ ← Most: Domain logic, value objects, use cases
```

## Coverage Requirements
| Layer | Tool | Minimum Coverage |
|-------|------|-----------------|
| Domain (Java) | JUnit 5 + AssertJ | 95% |
| Application (Java) | JUnit 5 + Mockito | 90% |
| Infrastructure (Java) | Testcontainers | 80% |
| API (Java) | MockMvc / WebTestClient | 85% |
| Python services | pytest | 80% |
| Frontend (TypeScript) | Vitest + Testing Library | 70% |

## Testing Patterns
1. **Domain layer**: Pure unit tests, no mocking framework needed, test domain events
2. **Application layer**: Mock domain repositories, test use case orchestration
3. **Infrastructure layer**: Testcontainers for PostgreSQL, Redpanda, Neo4j, Weaviate
4. **API layer**: Contract tests with Spring Cloud Contract or Pact
5. **E2E**: Docker Compose-based full stack tests for critical paths

## References
- ADR-005: DDD Modular Structure
- ADR-004: Event-Driven Architecture