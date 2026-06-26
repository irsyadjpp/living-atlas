# ADR-015: Database Schema and Naming Conventions

## Status
Accepted

## Context
Multiple developers and services contribute to the same database. Without consistent conventions, the schema becomes inconsistent and hard to maintain.

## Decision
We adopt strict naming conventions for all database objects: snake_case for names, explicit constraint names, and standard audit columns on every table.

## Rationale
- **Consistency**: Predictable naming improves developer productivity
- **Maintainability**: Constraint names make debugging easier
- **Audit compliance**: Standard audit columns on every table

## Conventions
| Object | Pattern | Example |
|--------|---------|---------|
| Table | `schema.table_name` | `content.stories` |
| Primary Key | `pk_{table}` | `pk_stories` |
| Foreign Key | `fk_{table}_{ref}` | `fk_stories_tenant` |
| Index | `idx_{table}_{field}` | `idx_stories_published_at` |
| Unique | `uq_{table}_{field}` | `uq_users_email` |
| Check | `chk_{table}_{rule}` | `chk_stories_type` |

## Standard Audit Columns
Every table MUST include:
```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
created_by UUID,
updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
updated_by UUID,
deleted_at TIMESTAMPTZ,
deleted_by UUID,
version BIGINT NOT NULL DEFAULT 1,
is_deleted BOOLEAN NOT NULL DEFAULT FALSE
```

## Schema Organization
| Schema | Purpose |
|--------|---------|
| `auth` | User authentication |
| `iam` | Identity & access management |
| `tenant` | Multi-tenancy |
| `source` | Content acquisition |
| `content` | Stories, articles |
| `knowledge` | Knowledge objects, themes, motifs |
| `culture` | Culture, beliefs, traditions |
| `research` | Collections, annotations |
| `ai` | AI pipeline state |
| `governance` | Audit, reviews, quality |
| `workflow` | State machines, approvals |
| `analytics` | Trends, insights |
| `system` | Outbox, configuration |

## References
- ddl.md - PostgreSQL DDL Strategy
- BACKEND-PRD.md §7 Audit Requirements