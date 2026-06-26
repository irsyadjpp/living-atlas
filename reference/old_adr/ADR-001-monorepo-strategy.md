# ADR-001: Monorepo Strategy

## Status
Accepted

## Context
The Living Atlas platform consists of multiple services (gateway, identity, content, knowledge, research, workflow), AI platform services, data platform, and frontend applications. We need a repository strategy that enables code sharing, unified versioning, and simplified CI/CD while maintaining service independence.

## Decision
We will use a monorepo structure managed with a single Git repository.

## Rationale
- **Small team**: Current team size does not warrant polyrepo overhead
- **Shared domain model**: Services share event schemas, types, and security contracts
- **Rapid iteration**: Atomic commits across services enable coordinated changes
- **Reduced operational complexity**: Single CI/CD pipeline, single issue tracker
- **Consistent tooling**: Unified build tool configuration and dependency management

## Consequences
### Positive
- Simplified dependency management across services
- Atomic cross-service refactoring
- Unified CI/CD with consistent quality gates
- Easier onboarding for new developers

### Negative
- Git history size grows faster
- CI triggers need careful path filtering
- Requires discipline in service boundaries to prevent coupling

## Implementation
```
living-atlas/
├── apps/           # Frontend applications
├── services/       # Backend services (Spring Boot)
├── ai-platform/    # AI pipeline services (Python)
├── data-platform/  # Data sync & analytics
├── packages/       # Shared libraries
├── infrastructure/ # Docker, K8s, Terraform
├── docs/           # Architecture & ADR
└── scripts/        # Dev & CI scripts
```

## References
- plan.md - Repository Structure
- BACKEND-PRD.md - Architecture Principles