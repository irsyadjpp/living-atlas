# ADR-014: API Versioning Strategy

## Status
Accepted

## Context
The platform will evolve over time. Breaking changes to APIs must be managed without disrupting existing clients. We need a versioning strategy that balances stability with velocity.

## Decision
We use URL-path versioning (`/api/v1/`, `/api/v2/`) for major versions, with backward-compatible minor changes within a version.

## Rationale
- **Explicit**: Version is visible in the URL, no header negotiation
- **Simple**: Easy to implement in gateway routing
- **Cache-friendly**: Different versions have different cache keys
- **Gradual migration**: Old and new versions can coexist

## Versioning Rules
1. **Major version** (`v1`, `v2`): Breaking changes (field removal, type changes, endpoint removal)
2. **Minor version** (within v1): Backward-compatible additions (new fields, new endpoints)
3. **Patch**: Bug fixes, no contract changes
4. **Deprecation**: Announce deprecation 6 months before removal
5. **Sunset**: Old versions supported for minimum 12 months

## Backward Compatibility Rules
- Adding optional fields: allowed
- Adding new endpoints: allowed
- Removing fields: major version only
- Changing field types: major version only
- Renaming fields: major version only
- Changing error codes: patch with documentation

## Implementation
```yaml
# Gateway route example
spring:
  cloud:
    gateway:
      routes:
        - id: stories-v1
          uri: lb://content-service
          predicates:
            - Path=/api/v1/stories/**
        - id: stories-v2
          uri: lb://content-service-v2
          predicates:
            - Path=/api/v2/stories/**
```

## References
- ADR-012: API Gateway Pattern
- BACKEND-PRD.md §6 Non Functional Requirements