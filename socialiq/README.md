# SOCIALIQ

**From Social Signals to Actionable Intelligence.**

SOCIALIQ is an agentic AI-powered social intelligence platform that transforms multi-platform social-media data into evidence-backed, actionable insights through a conversational interface.

## Architecture

```
Conversational UI → Master AI Agent (n8n) → Data Pipeline → AI/ML Analytics
→ Evidence Correlation → LLM Reasoning → Visualization → Blockchain Provenance
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js + React |
| Backend | Python + FastAPI |
| Orchestration | n8n |
| Database | PostgreSQL + pgvector |
| Graph | Neo4j |
| Cache | Redis |
| ML | Hugging Face Transformers, BERTopic |
| Blockchain | SHA-256 provenance ledger |

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
docker compose -f docker/docker-compose.yml up -d
```

### 3. Backend

```bash
cd socialiq
python -m venv backend/venv
backend/venv/Scripts/activate   # Windows
# source backend/venv/bin/activate  # macOS/Linux
pip install -r backend/requirements.txt
python run_backend.py
```

API runs at [http://localhost:8000](http://localhost:8000) — docs at `/docs`.

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

### 5. n8n (optional)

n8n runs at [http://localhost:5678](http://localhost:5678). Import workflows from `workflows/n8n/`.

## MVP Scope

- **Platforms:** X + Telegram (+ sample data fallback)
- **Analytics:** Sentiment, emotion, topics, trends, demographics, influence
- **Agents:** Master, Data Acquisition, Data Intelligence, Social Intelligence, Insight, Provenance
- **UI:** Chat + charts + trend visualization + network graph
- **Blockchain:** Dataset hash, insight hash, verification

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
├── ml/                # NLP, sentiment, trends, forecasting
├── graph/             # Neo4j network analytics
├── blockchain/        # Provenance & verification
├── workflows/n8n/     # n8n workflow definitions
├── docker/            # Docker Compose & configs
└── tests/
```

## License

Hackathon project — SIH 2026
