Saya menyarankan sedikit perubahan struktur dokumen ini terlebih dahulu.

Daftar yang Anda buat sebenarnya mencampur **end-user**, **organization**, dan **machine consumer**. Agar dokumen tetap konsisten selama puluhan halaman, saya sarankan mengelompokkannya terlebih dahulu.

```text
03-target-users.md

1. Introduction

2. User Classification

Group A — Public Readers
- Reader
- Horror Fans
- Podcast Audience
- Folklore Enthusiast

Group B — Professional Research
- Researcher
- Anthropologist
- Historian
- Journalist

Group C — Creative Industry
- Writer
- Film Director
- Producer
- Comic Artist
- Game Studio
- Content Creator

Group D — Institutions
- Museum
- School
- University
- Government
- Community

Group E — Machine Consumer
- AI Agent

3. Cross User Comparison

4. Design Implications
```

Karena setiap user memiliki sekitar 9 subbagian, satu dokumen akan mencapai ±50–70 halaman, yang memang sesuai target Anda.

---

Untuk **setiap user**, saya juga menyarankan template yang lebih lengkap agar seluruh tim (Product, UX, Backend, AI Platform) bisa menggunakan dokumen yang sama.

```text
Name

Overview

Primary Goals

Success Definition

Pain Points

Knowledge Level

Typical Workflow

Daily Activities

Discovery Journey

Search Behaviour

Reading Behaviour

Content Contribution

AI Usage

Expected Features

Key Metrics (KPIs)

Design Implications
```

Ini jauh lebih berguna daripada persona UX tradisional.

---

Saya juga menyarankan **AI Agent** ditempatkan terakhir, karena ia bukan manusia tetapi tetap merupakan "user" sistem.

Dokumen ini nantinya akan menjadi referensi utama untuk:

* Product roadmap
* Frontend UX
* Search
* AI Discovery
* RAG
* Prompt Engineering
* API Design

Sehingga tidak ada fitur yang dibuat tanpa mengetahui siapa konsumennya terlebih dahulu.
