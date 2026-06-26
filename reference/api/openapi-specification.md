# API Contract Specification

## OpenAPI 3.1
## Version 1.0
## Status: Draft

---

# Overview

This document defines the REST API contracts for all backend services in The Living Atlas platform. All APIs are accessed through the gateway-service at `/api/v1/`.

**Base URL**: `https://api.livingatlas.id/api/v1`

**Authentication**: JWT Bearer Token in `Authorization` header

**Content-Type**: `application/json`

---

# Common Patterns

## Pagination
```json
{
  "data": [],
  "pagination": {
    "page": 1,
    "pageSize": 20,
    "totalItems": 100,
    "totalPages": 5,
    "hasNext": true,
    "hasPrev": false
  }
}
```

## Error Response
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [
      {
        "field": "email",
        "message": "must be a valid email address"
      }
    ],
    "traceId": "abc123-def456"
  }
}
```

## Standard Headers
| Header | Description | Required |
|--------|-------------|----------|
| `Authorization` | Bearer JWT token | Yes (except public endpoints) |
| `X-Tenant-Id` | Tenant context | Yes (multitenant endpoints) |
| `X-Workspace-Id` | Workspace context | Optional |
| `X-Request-Id` | Idempotency/correlation | Recommended |
| `Accept-Language` | Localization | Optional |

---

# Identity Service

## Authentication

### POST /auth/register
Register a new user account.

```json
// Request
{
  "email": "user@example.com",
  "username": "researcher1",
  "password": "SecureP@ss123",
  "displayName": "Researcher One",
  "tenantSlug": "my-organization"
}

// Response 201
{
  "userId": "uuid",
  "email": "user@example.com",
  "username": "researcher1",
  "status": "pending",
  "emailVerificationToken": "uuid",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### POST /auth/login
Authenticate and receive JWT tokens.

```json
// Request
{
  "email": "user@example.com",
  "password": "SecureP@ss123"
}

// Response 200
{
  "accessToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIs...",
  "expiresIn": 900,
  "tokenType": "Bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "researcher1",
    "roles": ["researcher"],
    "tenants": [
      {
        "id": "uuid",
        "slug": "my-organization",
        "name": "My Organization"
      }
    ]
  }
}
```

### POST /auth/refresh
Refresh access token.

```json
// Request
{
  "refreshToken": "eyJhbGciOiJSUzI1NiIs..."
}

// Response 200
{
  "accessToken": "eyJhbGciOiJSUzI1NiIs...",
  "refreshToken": "eyJhbGciOiJSUzI1NiIs...",
  "expiresIn": 900
}
```

### POST /auth/logout
Invalidate current session.

```json
// Request
{
  "refreshToken": "eyJhbGciOiJSUzI1NiIs..."
}

// Response 204 (No Content)
```

## Users

### GET /users/me
Get current user profile.

```json
// Response 200
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "researcher1",
  "displayName": "Researcher One",
  "avatarUrl": "https://cdn.livingatlas.id/avatars/uuid.jpg",
  "status": "active",
  "emailVerified": true,
  "lastLoginAt": "2026-06-19T15:00:00Z",
  "roles": ["researcher"],
  "tenants": [],
  "createdAt": "2026-06-01T00:00:00Z"
}
```

### PATCH /users/me
Update user profile.

```json
// Request
{
  "displayName": "Updated Name",
  "avatarUrl": "https://cdn.livingatlas.id/avatars/new.jpg"
}

// Response 200
{
  "id": "uuid",
  "displayName": "Updated Name",
  "avatarUrl": "https://cdn.livingatlas.id/avatars/new.jpg"
}
```

## Tenants

### POST /tenants
Create a new tenant.

```json
// Request
{
  "slug": "research-lab-1",
  "name": "Research Lab 1",
  "tenantType": "research",
  "description": "Cultural research laboratory"
}

// Response 201
{
  "id": "uuid",
  "slug": "research-lab-1",
  "name": "Research Lab 1",
  "tenantType": "research",
  "status": "active",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### GET /tenants
List tenants (admin only).

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "slug": "research-lab-1",
      "name": "Research Lab 1",
      "tenantType": "research",
      "status": "active",
      "memberCount": 5
    }
  ],
  "pagination": {}
}
```

### GET /tenants/{tenantId}
Get tenant details.

```json
// Response 200
{
  "id": "uuid",
  "slug": "research-lab-1",
  "name": "Research Lab 1",
  "tenantType": "research",
  "status": "active",
  "subscriptionPlan": "professional",
  "description": "Cultural research laboratory",
  "metadata": {},
  "createdAt": "2026-06-20T01:00:00Z"
}
```

## Workspaces

### POST /tenants/{tenantId}/workspaces
Create workspace within tenant.

```json
// Request
{
  "slug": "folklore-study",
  "name": "Folklore Study 2026",
  "workspaceType": "research",
  "visibility": "private",
  "description": "Research workspace for folklore collection"
}

// Response 201
{
  "id": "uuid",
  "tenantId": "uuid",
  "slug": "folklore-study",
  "name": "Folklore Study 2026",
  "visibility": "private",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

## Roles & Permissions

### GET /roles
List all roles.

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "code": "system_admin",
      "name": "System Administrator",
      "description": "Full system access"
    },
    {
      "id": "uuid",
      "code": "tenant_admin",
      "name": "Tenant Administrator",
      "description": "Tenant-level administration"
    },
    {
      "id": "uuid",
      "code": "researcher",
      "name": "Researcher",
      "description": "Research workspace access"
    },
    {
      "id": "uuid",
      "code": "editor",
      "name": "Editor",
      "description": "Content creation and editing"
    },
    {
      "id": "uuid",
      "code": "reviewer",
      "name": "Reviewer",
      "description": "Content review and approval"
    },
    {
      "id": "uuid",
      "code": "creator",
      "name": "Creator",
      "description": "Content creation only"
    },
    {
      "id": "uuid",
      "code": "reader",
      "name": "Reader",
      "description": "Read-only access"
    }
  ]
}
```

### POST /users/{userId}/roles
Assign role to user.

```json
// Request
{
  "roleId": "uuid",
  "tenantId": "uuid",
  "workspaceId": "uuid (optional)"
}

// Response 204
```

---

# Content Service

## Stories

### POST /stories
Create a new story.

```json
// Request
{
  "title": "The Legend of Kuntilanak in Pontianak",
  "summary": "A traditional folklore about...",
  "storyType": "folklore",
  "canonicalSourceVideoId": "uuid",
  "languageCode": "id",
  "metadata": {
    "region": "West Kalimantan",
    "era": "contemporary"
  }
}

// Response 201
{
  "id": "uuid",
  "slug": "the-legend-of-kuntilanak-in-pontianak",
  "title": "The Legend of Kuntilanak in Pontianak",
  "storyType": "folklore",
  "status": "draft",
  "version": 1,
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### GET /stories
List stories with filtering.

```json
// Query Parameters
// ?page=1&pageSize=20&type=folklore&status=published&q=search+term

// Response 200
{
  "data": [
    {
      "id": "uuid",
      "slug": "the-legend-of-kuntilanak",
      "title": "The Legend of Kuntilanak in Pontianak",
      "storyType": "folklore",
      "status": "published",
      "confidenceScore": 0.85,
      "entityCount": 5,
      "themeCount": 3,
      "createdAt": "2026-06-20T01:00:00Z",
      "updatedAt": "2026-06-20T02:00:00Z"
    }
  ],
  "pagination": {}
}
```

### GET /stories/{storyId}
Get story details with full content.

```json
// Response 200
{
  "id": "uuid",
  "slug": "the-legend-of-kuntilanak-in-pontianak",
  "title": "The Legend of Kuntilanak in Pontianak",
  "summary": "A traditional folklore about...",
  "storyType": "folklore",
  "status": "published",
  "confidenceScore": 0.85,
  "canonicalSourceVideoId": "uuid",
  "metadata": {},
  "version": 3,
  "currentVersion": {
    "id": "uuid",
    "versionNumber": 3,
    "content": {
      "narrative": "Story content...",
      "segments": []
    },
    "createdAt": "2026-06-20T02:00:00Z",
    "createdBy": "uuid"
  },
  "evidence": [
    {
      "id": "uuid",
      "transcriptSegmentId": "uuid",
      "evidenceLevel": "direct",
      "confidenceScore": 0.95,
      "segmentContent": "In Pontianak, they say Kuntilanak...",
      "startSeconds": 125.5,
      "endSeconds": 135.2
    }
  ],
  "entities": [
    {
      "entityId": "uuid",
      "name": "Kuntilanak",
      "type": "spirit",
      "confidenceScore": 0.95
    }
  ],
  "themes": [
    {
      "themeId": "uuid",
      "name": "Fear",
      "weight": 0.9
    }
  ],
  "createdAt": "2026-06-20T01:00:00Z",
  "updatedAt": "2026-06-20T02:00:00Z"
}
```

### PATCH /stories/{storyId}
Update story metadata.

```json
// Request
{
  "title": "Updated Title",
  "summary": "Updated summary"
}

// Response 200
{
  "id": "uuid",
  "title": "Updated Title",
  "version": 4
}
```

### POST /stories/{storyId}/versions
Create new story version.

```json
// Request
{
  "content": {
    "narrative": "Updated story content...",
    "segments": []
  }
}

// Response 201
{
  "id": "uuid",
  "storyId": "uuid",
  "versionNumber": 4,
  "createdAt": "2026-06-20T03:00:00Z"
}
```

### GET /stories/{storyId}/versions
List all versions of a story.

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "versionNumber": 1,
      "createdAt": "2026-06-20T01:00:00Z",
      "createdBy": "uuid"
    },
    {
      "id": "uuid",
      "versionNumber": 2,
      "createdAt": "2026-06-20T01:30:00Z",
      "createdBy": "uuid"
    }
  ]
}
```

### DELETE /stories/{storyId}
Soft delete a story.

```json
// Response 204
```

## Articles

### POST /articles
Create or request article generation.

```json
// Request
{
  "storyId": "uuid",
  "articleType": "narrative",
  "title": "The Kuntilanak: Indonesia's Most Famous Ghost",
  "metadata": {
    "style": "journalistic",
    "targetAudience": "general"
  }
}

// Response 201
{
  "id": "uuid",
  "storyId": "uuid",
  "articleType": "narrative",
  "status": "generating",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### GET /articles/{articleId}
Get article.

```json
// Response 200
{
  "id": "uuid",
  "storyId": "uuid",
  "articleType": "narrative",
  "title": "The Kuntilanak: Indonesia's Most Famous Ghost",
  "status": "published",
  "content": "Full article content...",
  "metadata": {},
  "createdAt": "2026-06-20T01:00:00Z"
}
```

## Sources

### POST /sources/channels
Register a content channel.

```json
// Request
{
  "platform": "youtube",
  "platformChannelId": "UC123456789",
  "name": "Jurnal Risa Official",
  "description": "Indonesian mystery investigation channel",
  "languageCode": "id",
  "countryCode": "ID"
}

// Response 201
{
  "id": "uuid",
  "platform": "youtube",
  "platformChannelId": "UC123456789",
  "name": "Jurnal Risa Official",
  "slug": "jurnal-risa-official",
  "status": "active"
}
```

### GET /sources/channels
List registered channels.

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "platform": "youtube",
      "name": "Jurnal Risa Official",
      "slug": "jurnal-risa-official",
      "videoCount": 150,
      "subscriberCount": 2500000,
      "lastCrawledAt": "2026-06-19T12:00:00Z"
    }
  ],
  "pagination": {}
}
```

### GET /sources/videos
List videos with filtering.

```json
// Query Parameters
// ?channelId=uuid&status=transcribed&page=1&pageSize=20

// Response 200
{
  "data": [
    {
      "id": "uuid",
      "channelId": "uuid",
      "title": "MISTERI KUNTILANAK DI PONTIANAK",
      "publishedAt": "2026-06-01T00:00:00Z",
      "durationSeconds": 1800,
      "viewCount": 500000,
      "transcriptStatus": "completed",
      "storyCount": 3
    }
  ],
  "pagination": {}
}
```

---

# Knowledge Service

## Knowledge Objects

### GET /knowledge/objects
Query knowledge objects.

```json
// Query Parameters
// ?type=spirit&q=Kuntilanak&page=1&pageSize=20

// Response 200
{
  "data": [
    {
      "id": "uuid",
      "objectType": "entity",
      "entityType": "spirit",
      "canonicalName": "Kuntilanak",
      "summary": "A vengeful female spirit in Indonesian folklore...",
      "slug": "kuntilanak",
      "confidenceScore": 0.95,
      "aliases": [
        {"name": "Pontianak", "languageCode": "id"},
        {"name": "Kuntilanak", "languageCode": "id"}
      ],
      "storyCount": 25,
      "status": "active"
    }
  ],
  "pagination": {}
}
```

### GET /knowledge/objects/{objectId}
Get knowledge object with full details.

```json
// Response 200
{
  "id": "uuid",
  "objectType": "entity",
  "canonicalName": "Kuntilanak",
  "slug": "kuntilanak",
  "summary": "A vengeful female spirit in Indonesian folklore...",
  "description": "Kuntilanak is a mythological creature...",
  "entityType": "spirit",
  "confidenceScore": 0.95,
  "status": "active",
  "aliases": [],
  "culture": {
    "id": "uuid",
    "name": "Malay",
    "region": "Sumatra, Kalimantan"
  },
  "beliefs": [
    {"name": "Ancestral Spirit", "description": "..."}
  ],
  "traditions": [],
  "relatedEntities": [
    {
      "id": "uuid",
      "name": "Pontianak",
      "relation": "appears_in",
      "type": "location"
    }
  ],
  "stories": [
    {
      "id": "uuid",
      "title": "The Legend of Kuntilanak",
      "relevanceScore": 0.95
    }
  ],
  "versions": 3,
  "createdAt": "2026-06-01T00:00:00Z"
}
```

### POST /knowledge/objects
Create knowledge object (manual).

```json
// Request
{
  "objectType": "entity",
  "entityType": "spirit",
  "canonicalName": "Kuntilanak",
  "summary": "A vengeful female spirit...",
  "metadata": {}
}

// Response 201
{
  "id": "uuid",
  "slug": "kuntilanak",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

## Themes

### GET /knowledge/themes
List all themes.

```json
// Response 200
{
  "data": [
    {"id": "uuid", "name": "Fear", "slug": "fear", "storyCount": 120},
    {"id": "uuid", "name": "Loss", "slug": "loss", "storyCount": 85},
    {"id": "uuid", "name": "Afterlife", "slug": "afterlife", "storyCount": 95}
  ]
}
```

## Claims

### GET /knowledge/claims
List claims with filtering.

```json
// Query Parameters
// ?entityId=uuid&status=unverified&page=1

// Response 200
{
  "data": [
    {
      "id": "uuid",
      "claimText": "Kuntilanak originates from Dayak mythology",
      "claimType": "origin",
      "confidenceScore": 0.75,
      "status": "unverified",
      "evidenceCount": 3,
      "sources": [
        {
          "storyId": "uuid",
          "storyTitle": "Dayak Folklore Collection",
          "evidenceLevel": "derived",
          "confidenceScore": 0.8
        }
      ]
    }
  ],
  "pagination": {}
}
```

## Search

### GET /search
Full-text and semantic search.

```json
// Query Parameters
// ?q=kuntilanak origin&type=all&page=1&pageSize=20

// Response 200
{
  "data": [
    {
      "type": "knowledge_object",
      "id": "uuid",
      "title": "Kuntilanak",
      "snippet": "...originates from Dayak mythology...",
      "score": 0.95
    },
    {
      "type": "story",
      "id": "uuid",
      "title": "The Legend of Kuntilanak",
      "snippet": "...in Pontianak, they say Kuntilanak...",
      "score": 0.89
    }
  ],
  "pagination": {}
}
```

---

# Research Service

## Collections

### POST /research/collections
Create research collection.

```json
// Request
{
  "name": "Pontianak Folklore Study",
  "description": "Collection of stories about Pontianak",
  "visibility": "team"
}

// Response 201
{
  "id": "uuid",
  "name": "Pontianak Folklore Study",
  "itemCount": 0,
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### POST /research/collections/{collectionId}/items
Add item to collection.

```json
// Request
{
  "itemType": "story",
  "itemId": "uuid",
  "notes": "Key story about Kuntilanak origin"
}

// Response 201
```

## Annotations

### POST /research/annotations
Create annotation.

```json
// Request
{
  "targetType": "story",
  "targetId": "uuid",
  "content": "This segment shows clear connection to Dayak mythology",
  "startOffset": 120,
  "endOffset": 180,
  "tags": ["mythology", "dayak", "origin"]
}

// Response 201
{
  "id": "uuid",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

---

# Workflow Service

## Reviews

### POST /workflow/reviews
Submit content for review.

```json
// Request
{
  "targetType": "story",
  "targetId": "uuid",
  "reviewerId": "uuid",
  "notes": "Please review for accuracy",
  "priority": "normal"
}

// Response 201
{
  "id": "uuid",
  "status": "pending",
  "createdAt": "2026-06-20T01:00:00Z"
}
```

### POST /workflow/reviews/{reviewId}/approve
Approve content.

```json
// Request
{
  "notes": "Content verified against source transcript",
  "decision": "approved"
}

// Response 200
{
  "id": "uuid",
  "status": "approved",
  "approvedAt": "2026-06-20T02:00:00Z"
}
```

### POST /workflow/reviews/{reviewId}/reject
Reject content.

```json
// Request
{
  "notes": "Missing source citation for key claim",
  "decision": "rejected",
  "requiredChanges": [
    "Add citation for Kuntilanak origin story"
  ]
}

// Response 200
{
  "id": "uuid",
  "status": "rejected",
  "rejectedAt": "2026-06-20T02:00:00Z"
}
```

### GET /workflow/reviews
List reviews for current user.

```json
// Response 200
{
  "data": [
    {
      "id": "uuid",
      "targetType": "story",
      "targetTitle": "The Legend of Kuntilanak",
      "status": "pending",
      "requestedBy": {"id": "uuid", "name": "Editor 1"},
      "createdAt": "2026-06-20T01:00:00Z"
    }
  ],
  "pagination": {}
}
```

---

# Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Missing or invalid authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource already exists |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |
| TENANT_QUOTA_EXCEEDED | 403 | Tenant resource limit reached |
| WORKFLOW_INVALID_TRANSITION | 409 | Invalid state transition |

---

# Rate Limiting

| Tier | Rate Limit | Burst |
|------|-----------|-------|
| Public | 100 req/min | 200 |
| Authenticated | 500 req/min | 1000 |
| Premium Tenant | 2000 req/min | 4000 |
| Internal Service | 10000 req/min | 20000 |

Rate limit headers returned:
```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 423
X-RateLimit-Reset: 1624168800
```

---

# References

- ADR-012: API Gateway Pattern
- ADR-014: API Versioning Strategy
- ADR-016: Security Architecture
- BACKEND-PRD.md §3 Functional Domains