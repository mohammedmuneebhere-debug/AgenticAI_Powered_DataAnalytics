# SOCIALIQ

**From Social Signals to Actionable Intelligence.**

SOCIALIQ is an agentic AI-powered social intelligence platform that transforms multi-platform social-media data into evidence-backed, actionable insights through a conversational interface.

## Architecture

```
Next.js UI → FastAPI → Master Agent (hand-written async planner)
  → Data Acquisition (X/Apify, Telegram, Instagram, Pinterest, Reddit, SerpAPI, News)
  → Normalization → [Social ‖ Domain analytics, concurrent] → Evidence Correlation
  → Embeddings (pgvector) → Visualization → LLM Insight → Provenance (hash chain + IPFS)
```

The master planner is custom Python (`agents/master/planner.py`), not an
orchestration framework. n8n is an optional integration surface for external
triggers, not the request path. Full topology, stage table and the list of
components deliberately **not** built: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Tech Stack

| Layer | Technology | Status |
|-------|------------|--------|
| Frontend | Next.js 16, React 18, Tailwind, Recharts | in use |
| Backend | Python 3.12, FastAPI, async planner | in use |
| Database | PostgreSQL 16 + pgvector, SQLAlchemy, Alembic | in use (JSON fallback) |
| Provenance | SHA-256 hash chain + IPFS (kubo) pinning | in use (IPFS best effort) |
| ML | VADER / cardiffnlp RoBERTa, spaCy NER, sentence-transformers (MiniLM), NetworkX, Prophet (opt-in) | in use |
| Cache | Redis (analysis cache, token blacklist) | optional |
| Graph DB | Neo4j mirror of the mention graph | optional (`GRAPH_STORE=neo4j`) |
| Integration | n8n | optional webhooks |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+
- Python 3.11+

### 1. Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys (OpenAI, X/Twitter, Telegram, etc.)
```

### 2. Start Infrastructure

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis neo4j ipfs
```

PostgreSQL (pgvector), Redis, Neo4j and a local IPFS node. All four are
**optional** — the API runs without them (see `JSON_FALLBACK` below).

### 3. Database Schema

```bash
.venv/Scripts/python -m alembic upgrade head      # Windows
# python -m alembic upgrade head                  # macOS/Linux
```

To switch users/chat from JSON files to PostgreSQL, set `JSON_FALLBACK=false` in
`.env` and (once) migrate existing data:

```bash
.venv/Scripts/python scripts/seed_postgres.py
```

### 4. Backend

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate    # macOS/Linux
pip install -r backend/requirements.txt
python run_backend.py
```

API runs at [http://localhost:8000](http://localhost:8000) — docs at `/docs`.

### 5. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 6. n8n (optional)

n8n runs at [http://localhost:5678](http://localhost:5678). Import workflows from `workflows/n8n/`.

## MVP Scope

- **Platforms:** X (API or Apify), Telegram, Instagram, Pinterest, Reddit, Google Search/Trends, NewsAPI (+ sample fallback)
- **Analytics:** VADER/RoBERTa sentiment, emotion, spaCy topics + NER, z-score trend velocity, audience segments from author metadata, NetworkX influence/communities
- **Semantic:** MiniLM embeddings in pgvector, near-duplicate collapse, cross-source corroboration, similar-records API
- **Agents:** Master, Data Acquisition, Data Intelligence, Social Intelligence, Domain, Visualization, Insight, Synthetic fallback, Provenance
- **UI:** Chat + intelligence dossier (charts, trend drivers, network graph, audience segments, provenance verification)
- **Provenance:** SHA-256 hash chain + IPFS pinning with a real verify endpoint

## Demo Queries

1. *"Analyze coffee trends and tell me what product I should launch this winter."*
2. *"Why is BTC volatile today and what scenarios should I prepare for?"*
3. *"Find trending content and create a strategy for the next 7 days."*

## Project Structure

```
socialiq/
├── frontend/          # Next.js chat UI + visualizations
├── backend/           # FastAPI API layer
├── agents/            # Multi-agent orchestration modules
├── ml/                # Sentiment, entities, topics, trends, correlation, embeddings
├── graph/             # NetworkX analytics + optional Neo4j mirror
├── blockchain/        # Hash-chain ledger + IPFS client
├── workflows/n8n/     # n8n workflow definitions
├── docker/            # Docker Compose & configs
├── migrations/        # Alembic migrations
├── scripts/           # seed_postgres.py (JSON -> PostgreSQL)
└── tests/
```

## License

Hackathon project — SIH 2026
