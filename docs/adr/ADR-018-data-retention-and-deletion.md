# ADR-018: Data Retention and Deletion Strategy

## Status
Accepted

## Context
Different data domains have different retention requirements. Knowledge objects must be preserved indefinitely for cultural heritage. User data has privacy requirements. Audit logs must be immutable.

## Decision
We implement a tiered data retention strategy: knowledge domain is never deleted, content/source domains use soft delete, governance domain is immutable, and user data follows GDPR-style deletion.

## Rationale
- **Cultural preservation**: Knowledge objects are cultural heritage, must persist
- **Research integrity**: Provenance chains must remain intact
- **Privacy compliance**: User data must be deletable on request
- **Audit requirements**: Governance data must be immutable

## Retention Rules
| Domain | Deletion Policy | Rationale |
|--------|----------------|-----------|
| Knowledge | Never Delete | Cultural heritage, provenance chains |
| Content | Soft Delete | Editorial flexibility, recovery |
| Source | Soft Delete | Provenance preservation |
| Governance | Never Delete | Audit compliance |
| Audit | Never Delete | Legal/regulatory |
| User Data | Hard Delete (GDPR) | Privacy compliance |
| AI Artifacts | Soft Delete | Reproducibility |

## Soft Delete Implementation
```sql
-- Every table includes:
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
deleted_at TIMESTAMPTZ
deleted_by UUID

-- Queries filter:
WHERE is_deleted = FALSE

-- Background job permanently removes after 90 days
```

## GDPR Deletion Flow
1. User requests deletion
2. Anonymize personal data (email, name → [deleted])
3. Preserve knowledge contributions (attribution becomes "anonymous")
4. Remove authentication credentials
5. Hard delete from auth.users after 30-day grace period

## References
- ddl.md - Soft Delete vs Hard Delete
- BACKEND-PRD.md §7 Audit Requirements