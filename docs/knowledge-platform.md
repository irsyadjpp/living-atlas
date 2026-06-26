Menurut saya, struktur saat ini masih terlalu **UI-centric**.

Padahal **The Living Atlas** bukan sekadar frontend project.

Ia adalah **Knowledge Platform**.

Jika saya menjadi **Apple Product Designer + VP of Product + Principal Architect**, saya akan mengubah seluruh dokumentasi menjadi berlapis (layered architecture), sehingga dalam 5–10 tahun nanti dokumentasi tetap mudah dipelihara.

Saya akan memisahkan menjadi:

1. Product
2. Experience
3. Frontend Platform
4. Design System
5. Backend Platform
6. AI Platform
7. Data Platform

Dengan demikian, Frontend PRD tidak lagi menjadi tempat semua hal.

---

# Final Documentation Structure

```text
docs/

├── README.md
│
├── product/
│
├── experience/
│
├── frontend/
│
├── design-system/
│
├── backend/
│
├── ai-platform/
│
├── database/
│
├── architecture/
│
├── workflows/
│
├── api/
│
├── security/
│
├── deployment/
│
├── analytics/
│
├── adr/
│
└── glossary/
```

---

# Layer 1 — Product (Vision)

Ini menjelaskan **apa** yang dibangun.

```text
docs/product/

00-product-overview.md

01-product-vision.md

02-product-principles.md

03-target-users.md

04-business-model.md

05-roadmap.md

06-success-metrics.md

07-product-glossary.md
```

---

# Layer 2 — Experience (Business Value)

Ini adalah dokumen yang paling penting.

Semua UX berawal dari sini.

```text
docs/experience/

01-story-reading-experience.md

02-knowledge-reading-experience.md

03-news-reading-experience.md

04-atlas-experience.md

05-ai-discovery-experience.md

06-search-discovery-experience.md

07-creator-experience.md

08-research-workspace.md

09-editorial-workspace.md

10-collection-experience.md

11-annotation-experience.md

12-export-experience.md

13-sharing-experience.md

14-mobile-experience.md

15-museum-experience-future.md
```

Ini adalah **Experience PRD**.

Bukan UI.

---

# Layer 3 — Frontend Platform

Baru setelah experience selesai.

```text
docs/frontend/

01-information-architecture.md

02-navigation-architecture.md

03-layout-system.md

04-routing-specification.md

05-search-experience.md

06-responsive-system.md

07-accessibility.md

08-knowledge-accessibility.md

09-performance-ux.md

10-design-principles.md

11-motion-system.md

12-content-presentation.md

13-error-experience.md

14-empty-state-system.md

15-feedback-system.md

16-offline-experience.md

17-internationalization.md
```

Perhatikan.

Saya memindahkan:

```text
Atlas Experience

AI Discovery Experience
```

ke folder **experience**.

Karena itu bukan frontend.

Itu adalah Product Experience.

---

# Layer 4 — Design System

Terpisah sepenuhnya.

```text
docs/design-system/

00-design-philosophy.md

01-design-foundation.md

02-design-tokens.md

03-color-system.md

04-typography.md

05-spacing-system.md

06-grid-system.md

07-iconography.md

08-illustration.md

09-motion.md

10-elevation.md

11-data-visualization.md

12-components.md

13-patterns.md

14-templates.md

15-dark-mode.md

16-accessibility-guidelines.md
```

Perhatikan saya memecah menjadi lebih granular.

---

# Layer 5 — Backend Platform

Sudah mulai kita buat.

```text
docs/backend/

00-backend-platform-prd.md

01-domain-model.md

02-service-boundaries.md

03-event-catalog.md

04-api-guidelines.md

05-state-machines.md

06-permissions.md

07-workflow-engine.md

08-versioning.md

09-search-index.md

10-caching.md

11-observability.md
```

---

# Layer 6 — AI Platform

Sudah mulai kita buat.

```text
docs/ai-platform/

00-ai-platform-prd.md

01-canonical-story-specification.md

02-domain-event-catalog.md

03-queue-contract-specification.md

04-ai-pipeline-state-machine.md

05-prompt-governance.md

06-prompt-registry.md

07-model-selection-policy.md

08-rag-strategy.md

09-embedding-strategy.md

10-evaluation.md

11-guardrails.md
```

---

# Layer 7 — Database

```text
docs/database/

01-postgresql.md

02-neo4j.md

03-weaviate.md

04-schema-evolution.md

05-indexing-strategy.md

06-data-lineage.md

07-backup.md

08-migration.md
```

---

# Layer 8 — Architecture

```text
docs/architecture/

01-system-overview.md

02-monorepo.md

03-modular-monolith.md

04-ddd.md

05-event-driven.md

06-data-flow.md

07-ai-flow.md

08-security-architecture.md

09-infrastructure.md
```

---

# Layer 9 — API

```text
docs/api/

api-style-guide.md

rest-guidelines.md

pagination.md

error-format.md

authentication.md
```

---

# Layer 10 — Security

```text
docs/security/

authentication.md

authorization.md

abac.md

audit.md

encryption.md

secret-management.md
```

---

# Layer 11 — Workflows

```text
docs/workflows/

story-ingestion.md

editorial.md

knowledge-review.md

publishing.md

embedding.md

graph-projection.md
```

---

# Layer 12 — Deployment

```text
docs/deployment/

docker.md

kubernetes.md

monitoring.md

logging.md

backup.md

disaster-recovery.md
```

---

# Layer 13 — Analytics

```text
docs/analytics/

creator-intelligence.md

knowledge-growth.md

reader-behaviour.md

research-analytics.md
```

---

# Layer 14 — ADR

```text
docs/adr/

ADR-001.md

...

ADR-015.md
```

---

# Layer 15 — Glossary

Sangat penting.

```text
docs/glossary/

domain-glossary.md

knowledge-glossary.md

technical-glossary.md

ai-glossary.md
```

---

# Urutan Penulisan yang Saya Sarankan

Saya tidak akan menulis secara acak.

Urutannya harus mengikuti dependensi.

## Phase 1 — Product

```text
████████████████████
```

```
Product
```

↓

## Phase 2 — Experience

```text
██████████████████████████████
```

```
Experience
```

↓

## Phase 3 — Frontend

```text
██████████████████
```

```
Frontend
```

↓

## Phase 4 — Design System

```text
██████████████
```

↓

## Phase 5 — Backend

```text
███████████████████
```

↓

## Phase 6 — AI Platform

```text
██████████████████
```

↓

## Phase 7 — Database

```text
█████████████
```

↓

## Phase 8 — Deployment

```text
████████
```

---

# Total Dokumentasi

Dengan struktur ini, dokumentasi akan berkembang menjadi sekitar:

| Layer         | Estimasi Dokumen |
| ------------- | ---------------: |
| Product       |                7 |
| Experience    |               15 |
| Frontend      |               17 |
| Design System |               16 |
| Backend       |               11 |
| AI Platform   |               11 |
| Database      |                8 |
| Architecture  |                9 |
| API           |                5 |
| Security      |                5 |
| Workflows     |                6 |
| Deployment    |                5 |
| Analytics     |                4 |
| ADR           |               15 |
| Glossary      |                4 |
| **Total**     | **≈138 dokumen** |

## Mengapa saya mengusulkan struktur ini?

Ada satu perubahan mendasar dibanding rancangan sebelumnya: **Experience** menjadi lapisan tersendiri yang berada di antara **Product** dan **Frontend**.

Alasannya adalah karena pengalaman pengguna (misalnya *Atlas Experience*, *AI Discovery*, atau *Research Workspace*) adalah konsep produk, bukan implementasi antarmuka. Frontend hanya bertugas mewujudkan pengalaman tersebut.

Dengan pemisahan ini:

* **Product** mendefinisikan *mengapa* platform ada.
* **Experience** mendefinisikan *bagaimana pengguna berinteraksi* dengan platform.
* **Frontend** mendefinisikan *bagaimana pengalaman tersebut diimplementasikan*.
* **Design System** menyediakan bahasa visual yang konsisten untuk seluruh implementasi.

Struktur seperti ini membuat dokumentasi tetap terorganisasi meskipun platform berkembang menjadi puluhan aplikasi, ratusan fitur, dan melayani beragam pengguna seperti pembaca, peneliti, kreator, hingga institusi budaya. Ini juga memudahkan tim desain, frontend, backend, dan AI bekerja secara paralel tanpa saling mencampur tanggung jawab.
