# SOCIALIQ Architecture

This document describes what the system **actually does**, not an aspirational
diagram. Every box below is implemented and exercised by the test suite; things
that are optional are labelled as such, with the flag that enables them.

## 1. Runtime topology

```
                ┌─────────────────────────────���───────────────────────────┐
                │  Next.js 16 frontend (chat + intelligence dossier)     │
                └───────────────────────────┬─────────────────────────────┘
                                            │ REST + Bearer JWT
                                            ▼
        ┌───────────────────────────────────────────────────────────────────┐
        │ FastAPI backend                                                   │
        │                                                                   │
        │  routes.py ──► OrchestratorService.process_query                  │
        │                   │                                               │
        │                   ▼                                               │
        │            MasterAgent.plan_and_execute  (custom planner)         │
        │                   │                                               │
        │   ┌───────────────┼───────────────┬───────────────┐               │
        │   ▼               ▼               ▼               ▼               │
        │  acquire ──► clean ──┬──► [social ‖ domain] ──► correlate        │
        │  (X/Apify,         │    (concurrent, isolated)   (statistical +   │
        │   Telegram,         │                            semantic)        │
        │   Instagram,        │                │                             │
        │   Pinterest,        │                ├──► embed ──► pgvector      │
        │   Reddit, SerpAPI,  │                │                             │
        │   NewsAPI, Trends)  │                ├──► NetworkX graph          │
        │                     │                │        (│ mirror to Neo4j)  │
        │                     ▼                ▼                             │
        │              visualization ◄── insight (LLM / offline composer)   │
        │                                                                   │
        │  chat_store / user_store ──► PostgreSQL (or JSON fallback)        │
        │  provenance ──► ledger (SHA-256 chain) ──► IPFS pin (best effort) │
        │  cache/blacklist ──► Redis (optional)                             │
        └───────────────────────────────────────────────────────────────────┘
```

### Pipeline stages (`agents/master/planner.py`)

| Stage | Component | Notes |
|-------|-----------|-------|
| 1 | `DataAcquisitionAgent` | Live APIs in parallel, sample-data fallback |
| 2 | `DataIntelligenceAgent` | Normalization, dedup, snapshot hash |
| 3 | `SocialIntelligenceAgent` **and** `DomainAnalyticsAgent` | Run **concurrently**; each has its own timeout and failure isolation |
| 4 | `_index_embeddings` | MiniLM vectors upserted into pgvector (idempotent by content hash) |
| 5 | `EvidenceCorrelationEngine` | Statistical + semantic (dedup collapse, cross-source corroboration) |
| 6 | `VisualizationAgent` | Chart specs for the dossier |
| 7 | `InsightAgent` | LLM reasoning, offline composer fallback |
| 8 | `SyntheticDataAgent` | Clearly-flagged fill for blank sections |
| 9 | `ProvenanceAgent` | Hash chain + IPFS pin |

A failing or slow stage degrades that section only; the response is still built
(`MasterAgent._run_stage`).

## 2. Data stores

| Store | Default | Alternative | Flag |
|-------|---------|-------------|------|
| Users, chat sessions/messages | JSON files (`data/*.json`) | PostgreSQL via SQLAlchemy | `JSON_FALLBACK=false` |
| Records / embeddings | - | PostgreSQL + pgvector (HNSW cosine) | automatic when PG is up |
| Provenance ledger | `data/ledger.json` hash chain | + IPFS pin on the same record | `IPFS_API_URL` |
| Analysis cache, token blacklist | - | Redis | `REDIS_URL` |
| Mention graph | in-memory NetworkX | mirrored to Neo4j | `GRAPH_STORE=neo4j` |

**Every optional store degrades gracefully.** With nothing but Docker stopped the
API still serves queries: JSON stores, no embeddings, no IPFS pin, no cache.

Schema changes are managed by Alembic (`alembic upgrade head`). The JSON stores
seed PostgreSQL once via `scripts/seed_postgres.py`; `docker/init-db.sql` only
provisions the `vector` extension.

## 3. ML stack (what actually runs)

| Module | Implementation | Flag |
|--------|----------------|------|
| Sentiment | VADER (default), cardiffnlp RoBERTa (lazy, falls back to VADER) | `ML_SENTIMENT_BACKEND` |
| Entities | spaCy `en_core_web_sm` NER, regex fallback | - |
| Topics | spaCy lemmatized noun clusters, regex fallback | - |
| Trends | Dataset-derived terms + mention-velocity z-scores, optional Prophet forecast | `TREND_FORECAST_ENABLED` |
| Demographics | Follower tiers, verified share, locations from author metadata + bio NER | computed when metadata exists |
| Graph | NetworkX PageRank + greedy modularity communities | `GRAPH_STORE` |
| Embeddings | all-MiniLM-L6-v2 (384-d), normalized | `EMBEDDING_MODEL` |

**Thresholds are calibrated, not guessed.** `ml/correlation.py` collapses
restatements of one signal at cosine >= 0.85, chosen from measured MiniLM bands
(restatements 0.90+, same topic different fact 0.60-0.70, unrelated < 0.15).

## 4. Provenance

Two independent layers:

1. **Hash chain (always on).** Each block hashes its content plus the previous
   block hash. `chain_integrity()` recomputes the whole chain and reports the
   first block that was edited.
2. **IPFS pin (best effort).** The canonical record bytes are pinned to the local
   kubo node; the CID is stored on the block *before* the block hash is computed,
   so it is covered by the chain too.

`POST /api/v1/provenance/verify` re-fetches the pinned bytes, recomputes SHA-256
and compares against the ledger. Records written while the node was down are
verified against the chain alone and are labelled `hash_chain` - never reported
as IPFS-verified.

## 5. What was deliberately dropped

The original stack diagram listed components the product never used. These are
**not** implemented, on purpose:

- **Kafka / Airflow / dbt** - the pipeline is a single-process async planner.
  A message bus and a DAG scheduler would add operational weight without
  changing behaviour. (Redis Streams as a real event backbone: deferred.)
- **Elasticsearch / OpenSearch** - pgvector with an HNSW cosine index covers the
  one query the product needs ("records semantically like this one").
- **LangChain / CrewAI / AutoGen** - the master planner is hand-written
  (`agents/master/planner.py`); the orchestration is ~300 lines of explicit
  `async` code with clearer failure semantics than a framework would give here.
- **Ethereum anchoring** - provenance stays local + IPFS; on-chain anchoring has
  no user-visible payoff at this stage.
- **BERTopic** - topic detection is spaCy lemmatization, which is sufficient at
  this corpus size.

## 6. Tests

```bash
.venv/Scripts/python -m pytest tests/ -q      # Windows
python -m pytest tests/ -q                     # macOS/Linux
```

Suite is Docker-independent: PostgreSQL, MiniLM and IPFS tests skip cleanly when
those services are absent, and the fallback paths they guard are tested with
explicit offline fakes.
