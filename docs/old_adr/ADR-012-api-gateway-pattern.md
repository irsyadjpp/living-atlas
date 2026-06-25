# ADR-012: API Gateway Pattern

## Status
Accepted

## Context
Frontend applications (web-atlas, web-admin, web-research, mobile) and external integrations need a single entry point to backend services. Direct service exposure creates security risks, coupling, and client complexity.

## Decision
We use a dedicated gateway-service (Spring Boot) as the single entry point for all client requests. It handles authentication, routing, rate limiting, and API aggregation.

## Rationale
- **Security**: Single point for auth enforcement, CORS, rate limiting
- **Abstraction**: Clients don't know about service topology
- **Cross-cutting**: Logging, metrics, tracing in one place
- **API versioning**: Managed at gateway level

## Consequences
### Positive
- Centralized security enforcement
- Simplified client integration
- Rate limiting at entry point
- Request/response transformation

### Negative
- Single point of failure (mitigated by redundancy)
- Additional network hop
- Gateway can become a bottleneck if not scaled

## Gateway Responsibilities
1. **Authentication**: Validate JWT tokens, delegate to identity-service
2. **Authorization**: Enforce ABAC decisions (delegated enforcement)
3. **Routing**: Proxy requests to appropriate backend service
4. **Rate Limiting**: Per-client, per-endpoint rate limits
5. **Aggregation**: Composite responses from multiple services
6. **CORS**: Manage cross-origin policies for web clients

## Route Table
```
/api/v1/auth/**        → identity-service
/api/v1/users/**       → identity-service
/api/v1/tenants/**     → identity-service
/api/v1/stories/**     → content-service
/api/v1/articles/**    → content-service
/api/v1/sources/**     → content-service
/api/v1/knowledge/**   → knowledge-service
/api/v1/research/**    → research-service
/api/v1/workflow/**    → workflow-service
/api/v1/search/**      → knowledge-service (Weaviate proxy)
/api/v1/graph/**       → knowledge-service (Neo4j proxy)
```

## References
- plan.md - gateway-service
- BACKEND-PRD.md §3 Identity Domain, §6 Non Functional Requirements