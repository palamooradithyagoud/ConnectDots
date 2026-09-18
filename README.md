# 🕵️‍♂️ ConnectDots — AI Crime Analysis & Intelligence Platform

> **"Understand the crime first. Connect the crimes later."**

**ConnectDots** is a full-stack, enterprise-grade AI Crime Analysis and Intelligence platform. Built with **FastAPI**, **PostgreSQL + PostGIS**, **Next.js 14 App Router**, **Sentence Transformers**, and **Qdrant Vector Database**, styled according to the **Innovators Conclave 2026** design language (Electric Violet `#5227ff`, Soft Lilac `#B19EEF`, and Deep Midnight `#0d0d1a`).

---

## 🏗️ System Architecture

```text
                               RAW CRIME DATASETS
                    (Inconsistent CSVs, JSON, Municipal Feeds)
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PHASE 1: Ingestion & Spatial Pipeline                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Ingestion Service (CSV/JSON Parser, Multi-format streaming)             │
│  2. Coordinate Bounds & Null Island Validator (-90/90, -180/180, (0.0, 0.0))│
│  3. Timestamp Parser (ISO-8601, US MM/DD/YYYY, European, 12h AM/PM -> UTC)  │
│  4. Canonical Taxonomy Engine (Maps 50+ raw aliases -> 10 Standard Types)   │
│  5. Text Sanitizer & Location Normalizer (Title Case, acronym retention)    │
│  6. Deduplication Engine (Intra-batch & DB fingerprint checks)              │
│  7. Two-Stage Pipeline: Dry-Run Diagnostics vs Transactional Commit         │
└──────────────────────┬───────────────────────────────┬──────────────────────┘
                       │                               │
            [Valid Records]                    [Rejected Records]
                       │                               │
                       ▼                               ▼
┌─────────────────────────────────────────┐  ┌────────────────────────────────┐
│       PostgreSQL 16 + PostGIS 3.3       │  │    Non-Destructive Rejection   │
│  • Table: `crimes`                      │  │  • Table: `crime_rejections`   │
│  • Coordinates: GEOGRAPHY(POINT, 4326)  │  │  • Stores batch ID, row number,│
│  • Spatial Index: GiST (fast geo radius)│  │    exact error & raw payload   │
│  • Table: `import_batches` (Audit logs) │  │  • Accessible via REST API     │
└──────────────────────┬──────────────────┘  └────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PHASE 2: NLP Understanding & Vector Pipeline                │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. Text Preprocessing Service (Unicode NFKD, whitespace, boilerplate strip)│
│     * Critical rule: Never mutates original source description               │
│  2. Entity Extraction Service (PERSON, LOCATION, ORG, VEHICLE, WEAPON, etc.)│
│  3. Canonical Classification Engine (10 Categories with confidence scores)  │
│  4. Modus Operandi Service (Explicitly stated vs Inferred behaviors)        │
│  5. Graph-Ready Service (Nodes & Edges structure prepared for Phase 4 Neo4j)│
│  6. Sentence Transformer Embeddings (`all-MiniLM-L6-v2`, 384 dimensions)    │
│  7. Qdrant Vector Database (Vector upsert & Cosine similarity retrieval)   │
│  8. Persistence: Stored in PostgreSQL `nlp_analyses` table                  │
└──────────────────────┬──────────────────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FastAPI Production Backend                         │
│  • /api/v1/health             • /api/v1/crimes/import                       │
│  • /api/v1/crimes             • /api/v1/crimes/stats                        │
│  • /api/v1/crimes/locations   • /api/v1/nlp/process & /nlp/stats            │
│  • /api/v1/search/similar (Natural language semantic search)                │
└──────────────────────┬──────────────────────────────────────────────────────┘
                       │ REST / GeoJSON
                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ConnectDots Command Center (Next.js 14)                   │
│  • Overview KPI Dashboard (/)        • Crime Explorer (/crimes)             │
│  • Semantic Crime Search (/search)   • Ingestion Pipeline (/import)         │
│  • PostGIS Geospatial Map (/map)     • Detail Drawer with NLP Intelligence  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Core Capabilities

### Phase 1: Data Collection & Preprocessing
* **Multi-Format Ingestion**: Ingests messy real-world CSVs and JSON streams with automatic batch tracking.
* **WGS84 Coordinate Sanity & PostGIS**: Validates geographical bounds and rejects the "Null Island" `(0.0, 0.0)` coordinate anomaly. Stores geometries as `GEOGRAPHY(POINT, 4326)` with high-speed GiST spatial indexes.
* **Non-Destructive Error Engine**: Rejections are never silently discarded. Every malformed row is logged in `crime_rejections` with exact line number, error reason, and raw payload.
* **Two-Stage Ingestion UX**: Dry-Run validation preview before transactional database commit.

### Phase 2: NLP & Crime Understanding
* **Preservation of Truth**: Original descriptions remain permanently untouched; processed forensic text is stored independently.
* **Entity Extraction**: Grounded extraction for `PERSON`, `LOCATION`, `ORGANIZATION`, `VEHICLE`, `WEAPON`, `DATE`, `TIME`, and `MONEY`. Zero-hallucination constraint.
* **Canonical Classification**: Predicts across 10 standard categories (`THEFT`, `BURGLARY`, `ROBBERY`, `ASSAULT`, `HOMICIDE`, `VEHICLE_THEFT`, `FRAUD`, `CYBERCRIME`, `NARCOTICS`, `VANDALISM`) with calibrated confidence and human-in-the-loop review flags.
* **Modus Operandi Detection**: Flags explicit execution behaviors (e.g. *Armed robbery*, *Forced entry*, *Escape using vehicle*, *ATM skimming*).
* **Sentence Transformers + Qdrant**: 384-dimensional dense semantic vectors (`all-MiniLM-L6-v2`) indexed in Qdrant for natural language search queries.
* **Semantic Crime Search (`/search`)**: Search incidents by narrative description, weapons used, or execution patterns with real-time similarity threshold tuning.
* **Graph-Ready Schema**: Builds structured nodes and relationships ready to feed **Neo4j** in Phase 4 without requiring Neo4j in Phase 2.

---

## 📂 Project Structure

```text
ConnectDots/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app & lifespan configuration
│   │   ├── api/v1/
│   │   │   ├── api.py               # API router registry
│   │   │   └── endpoints/
│   │   │       ├── crimes.py        # Crime CRUD, ingestion, GeoJSON, stats
│   │   │       ├── nlp.py           # NLP processing, batch runner, stats
│   │   │       └── search.py        # Semantic vector similarity search
│   │   ├── core/
│   │   │   └── config.py            # Pydantic Settings (PostGIS, NLP, Qdrant)
│   │   ├── db/
│   │   │   ├── session.py           # SQLAlchemy engine & session factory
│   │   │   └── base.py              # Declarative Base & model registry
│   │   ├── models/
│   │   │   ├── crime.py             # Crime, ImportBatch, CrimeRejection models
│   │   │   └── nlp_analysis.py      # NlpAnalysis model (entities, M.O., graph)
│   │   ├── schemas/
│   │   │   ├── crime.py             # Pydantic validation schemas (Phase 1)
│   │   │   └── nlp.py               # NLP & Semantic search schemas (Phase 2)
│   │   └── services/
│   │       ├── cleaning_service.py  # Coordinates, timestamps, category cleaner
│   │       ├── text_preprocessor.py # Unicode NFKD & narrative cleaning
│   │       ├── entity_extraction_service.py # High-precision entity extraction
│   │       ├── classification_service.py # Canonical category prediction
│   │       ├── modus_operandi_service.py # M.O. behavioral pattern detection
│   │       ├── graph_ready_service.py # Nodes/relationships for Phase 4 Neo4j
│   │       ├── embedding_service.py # Sentence Transformers singleton loader
│   │       ├── qdrant_service.py    # Qdrant collection, indexing & search
│   │       └── nlp_service.py       # Master NLP orchestrator
│   ├── tests/
│   │   ├── test_pipeline.py         # 9 Phase 1 pipeline tests
│   │   ├── test_api.py              # In-memory API integration tests
│   │   └── test_nlp.py              # NLP, embedding, and Qdrant tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx             # Overview KPI Command Center
│   │   │   ├── crimes/page.tsx      # Crime Incident Explorer & Drawer
│   │   │   ├── search/page.tsx      # Semantic Crime Search interface
│   │   │   ├── import/page.tsx      # Two-stage Ingestion Wizard
│   │   │   ├── map/page.tsx         # PostGIS Leaflet Geospatial Visualizer
│   │   │   └── layout.tsx           # Dark theme layout & brand metadata
│   │   ├── components/
│   │   │   ├── Navbar.tsx           # Header with ConnectDots logo & routes
│   │   │   ├── NLPAnalysisCard.tsx  # Rich NLP intelligence & graph card
│   │   │   ├── CrimeDetailModal.tsx # Incident drawer with embedded NLP
│   │   │   ├── MapView.tsx          # Leaflet spatial map component
│   │   │   └── StatCard.tsx         # High-contrast glassmorphic KPI cards
│   │   ├── lib/
│   │   │   ├── api.ts               # Phase 1 REST client
│   │   │   └── nlp-api.ts           # Phase 2 NLP & Semantic search client
│   │   └── types/
│   │       └── crime.ts             # TypeScript definitions
│   ├── public/
│   │   └── logo.png                 # ConnectDots official brand logo
│   └── package.json
├── data/
│   ├── sample_crimes_valid.csv      # Verified clean dataset
│   ├── sample_crimes_with_errors.csv# Dirty data edge-case test set
│   └── sample_crimes.json           # JSON streaming format
├── docker-compose.yml               # PostGIS + Qdrant + FastAPI + Next.js
└── README.md
```

---

## 🧪 Testing & Validation

Run the automated test suite across all Phase 1 and Phase 2 modules:

```bash
cd backend
python -m pytest tests/ -v
```

```text
============================== test session starts ==============================
tests/test_api.py::test_health_endpoint PASSED                           [  5%]
tests/test_api.py::test_dry_run_import_csv PASSED                        [ 11%]
tests/test_api.py::test_commit_import_csv PASSED                         [ 16%]
tests/test_nlp.py::test_text_preprocessor_clean PASSED                   [ 22%]
tests/test_nlp.py::test_entity_extraction_prompt_example PASSED          [ 27%]
tests/test_nlp.py::test_modus_operandi_extraction PASSED                 [ 33%]
tests/test_nlp.py::test_modus_operandi_forced_entry PASSED               [ 38%]
tests/test_nlp.py::test_classification_service_high_confidence PASSED    [ 44%]
tests/test_nlp.py::test_classification_service_low_confidence_flagged PASSED [ 50%]
tests/test_nlp.py::test_embedding_generation_shape PASSED                [ 55%]
tests/test_nlp.py::test_graph_ready_payload_generation PASSED            [ 61%]
tests/test_nlp.py::test_qdrant_service_in_memory_upsert_and_search PASSED [ 66%]
tests/test_pipeline.py::test_coordinate_validation_valid PASSED          [ 72%]
tests/test_pipeline.py::test_coordinate_validation_out_of_bounds PASSED  [ 77%]
tests/test_pipeline.py::test_coordinate_validation_null_island_and_strings PASSED [ 83%]
tests/test_pipeline.py::test_date_parsing_various_formats PASSED         [ 88%]
tests/test_pipeline.py::test_crime_canonicalization PASSED               [ 94%]
tests/test_pipeline.py::test_full_record_validation PASSED               [100%]

======================= 18 passed in 26.50s ====================================
```

---

## 🚀 Running ConnectDots

### Option A: Local Run

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python -m uvicorn app.main:app --port 8000 --reload
   ```
   * Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

2. **Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   * Web App: [http://localhost:3000](http://localhost:3000)

### Option B: Docker Compose
```bash
docker compose up --build -d
```
Spins up:
* **PostgreSQL 16 + PostGIS 3.4** on `localhost:5432`
* **Qdrant Vector Database** on `localhost:6333`
* **FastAPI Backend** on `localhost:8000`
* **Next.js Command Center** on `localhost:3000`

---

## 🧭 Roadmap
* [x] **Phase 1**: Data Collection, Cleaning, PostGIS Normalization & Ingestion Dashboard
* [x] **Phase 2**: NLP Understanding, Entity Extraction, Modus Operandi, Sentence Transformers, Qdrant Vector Search
* [ ] **Phase 3**: Crime Clustering, Spatiotemporal Hotspot Modeling, Modus Operandi Pattern Mining
* [ ] **Phase 4**: Neo4j Knowledge Graph Ingestion, Graph RAG, Investigative Relationship Discovery
