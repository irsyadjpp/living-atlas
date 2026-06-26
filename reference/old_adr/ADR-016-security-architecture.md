# ADR-016: Security Architecture

## Status
Accepted

## Context
The platform handles cultural knowledge that may include sensitive location data, user research, and editorial workflows. Security must protect data at rest, in transit, and in access control.

## Decision
We implement a defense-in-depth security architecture: JWT-based authentication, OAuth2 for external integrations, ABAC for fine-grained authorization, and encryption for data protection.

## Rationale
- **JWT + OAuth2**: Industry standard for API security
- **ABAC**: Required for complex multi-tenant knowledge platform (not just role-based)
- **Encryption**: Compliance requirement for user data and sensitive locations

## Security Layers
```
Internet → WAF → Gateway → Service → Database
  ↓          ↓       ↓         ↓         ↓
  TLS       Rules   JWT      ABAC      Encryption
                    Rate     Audit     RLS
                    Limiting Logging
```

## Authentication
- **Users**: JWT (access + refresh tokens), 15-min access, 7-day refresh
- **API Clients**: OAuth2 client credentials with scoped tokens
- **Service-to-Service**: Internal JWT with limited TTL (5 min)

## Authorization (ABAC)
1. Gateway validates JWT and extracts identity claims
2. Service evaluates ABAC policies based on:
   - Subject (role, tenant, workspace)
   - Resource (type, status, ownership)
   - Action (create, read, update, delete, approve)
   - Environment (IP, time, location sensitivity)
3. PostgreSQL RLS as defense-in-depth

## Encryption
| Layer | Mechanism |
|-------|-----------|
| In Transit | TLS 1.3 |
| At Rest (DB) | PostgreSQL TDE or pgcrypto |
| At Rest (Storage) | S3/Azure Blob server-side encryption |
| Sensitive Fields | Application-level encryption (location coordinates) |

## Sensitive Location Handling
- Real coordinates stored encrypted at application level
- Public view shows region/city level only
- Access to raw coordinates requires explicit permission

## References
- ddl.md - Locations table, sensitive location handling
- BACKEND-PRD.md §3 Identity Domain, §6 NFR Security