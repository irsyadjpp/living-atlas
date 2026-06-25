# ADR-017: Frontend Architecture

## Status
Accepted

## Context
The platform has multiple frontend applications (web-atlas, web-admin, web-research, web-studio) sharing common UI components, design tokens, and API clients. Without shared libraries, each app would duplicate code.

## Decision
All frontend applications use React 19 + Next.js 16 with a shared design system package and API client package from the monorepo.

## Rationale
- **Code sharing**: UI components, types, and API clients shared via packages/
- **Consistency**: Shared design system ensures visual consistency
- **Developer experience**: Monorepo tooling (Turborepo) for build orchestration
- **Performance**: Next.js provides SSR, SSG, and ISR for public pages

## Application Responsibilities
| App | Role | Auth Required | SSG/SSR |
|-----|------|--------------|---------|
| web-atlas | Public website | No (public) | SSG + ISR |
| web-admin | Editorial CMS | Yes | SSR |
| web-research | Research workspace | Yes | SSR |
| web-studio | Creative workspace | Yes | SSR |

## Shared Packages
```
packages/
├── design-system/    # Tailwind + Radix + Shadcn components
├── api-client/       # Typed API client (generated from OpenAPI)
├── shared-types/     # TypeScript interfaces matching backend DTOs
├── shared-events/    # Event type definitions
└── shared-security/  # JWT handling, CSRF, RBAC utilities
```

## State Management
- **Server state**: React Query (TanStack Query) for API data
- **Client state**: React Context for auth, tenant, workspace
- **Form state**: React Hook Form + Zod validation
- **Global state**: Zustand for complex UI state (if needed)

## References
- plan.md - Apps, Packages
- BACKEND-PRD.md - Target Stack