# SOCIALIQ Integration Guide

How to connect n8n, social APIs, and external services to SOCIALIQ.

---

## 1. n8n Automation

### What n8n does in SOCIALIQ
n8n is the **orchestration layer** — it coordinates agents, handles webhooks, retries, scheduling, and branching. Heavy ML stays in Python; n8n triggers the FastAPI pipeline.

### Setup steps

**Step 1 — Start n8n via Docker**
```bash
cd socialiq
docker compose -f docker/docker-compose.yml up n8n -d
```
Open: **http://localhost:5678** (login: `admin` / `socialiq123`)

**Step 2 — Import the workflow**
1. In n8n → **Workflows** → **Import from File**
2. Select: `socialiq/workflows/n8n/master_workflow.json`

**Step 3 — Activate the workflow**
Toggle **Active** in the top-right of the workflow editor.

**Step 4 — Test the webhook**
```bash
curl -X POST http://localhost:5678/webhook/socialiq \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Why is BTC volatile today?\"}"
```

### n8n → SOCIALIQ flow
```
User/Webhook → n8n Webhook node → HTTP Request (POST /api/v1/chat) → Respond to Webhook
```

### Key files
| File | Purpose |
|------|---------|
| `workflows/n8n/master_workflow.json` | Importable n8n workflow |
| `workflows/n8n/README.md` | Quick reference |
| `.env` → `N8N_WEBHOOK_URL` | Webhook URL for backend triggers |
| `docker/docker-compose.yml` | n8n service definition |

### n8n docs
- **n8n homepage:** https://n8n.io
- **Webhook node:** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.webhook/
- **HTTP Request node:** https://docs.n8n.io/integrations/builtin/core-nodes/n8n-nodes-base.httprequest/

---

## 2. Social & Data APIs

### Where to add API keys

Copy `.env.example` to `.env` in the project root:

```bash
cp .env.example .env
```

| Variable | Service | Get key at |
|----------|---------|------------|
| `OPENAI_API_KEY` | LLM (GPT) | https://platform.openai.com/api-keys |
| `X_BEARER_TOKEN` | X (Twitter) API v2 | https://developer.x.com/en/portal/dashboard |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot API | https://t.me/BotFather |
| `INSTAGRAM_ACCESS_TOKEN` | Instagram Graph API | https://developers.facebook.com/docs/instagram-api/getting-started |
| `INSTAGRAM_USER_ID` | Instagram Business Account ID | Same portal (Graph API Explorer) |
| `PINTEREST_ACCESS_TOKEN` | Pinterest API v5 | https://developers.pinterest.com/apps/ |
| `SERPAPI_API_KEY` | SerpAPI Google Search and Google Trends | https://serpapi.com/manage-api-key |
| `SERPAPI_GOOGLE_DOMAIN` | Google domain used for search localization | `google.com` |
| `SERPAPI_TRENDS_GEO` | Optional Google Trends country/region code | SerpAPI Google Trends docs |
| `SERPAPI_TRENDS_DATE` | Google Trends time window | `today 12-m` |
| `NEWS_API_KEY` | NewsAPI (optional) | https://newsapi.org/register |
| `REDDIT_CLIENT_ID` | Reddit API (optional) | https://www.reddit.com/prefs/apps |

### Where API calls live

| Platform | File | Method |
|----------|------|--------|
| **X (Twitter)** | `agents/data_acquisition/agent.py` | `_fetch_x()` |
| **Telegram** | `agents/data_acquisition/agent.py` | `_fetch_telegram()` |
| **Instagram** | `agents/data_acquisition/agent.py` | `_fetch_instagram()` |
| **Pinterest** | `agents/data_acquisition/agent.py` | `_fetch_pinterest()` |
| **Google Search** | `agents/data_acquisition/agent.py` | `_fetch_google_search()` |
| **Google Trends** | `agents/data_acquisition/agent.py` | `_fetch_google_trends()` |
| **Reddit** | `agents/data_acquisition/agent.py` | Add `_fetch_reddit()` |
| **News** | `agents/data_acquisition/agent.py` | Add `_fetch_news()` |
| **LLM (OpenAI)** | `agents/insight/agent.py` | Already wired via `_llm_generate()` |
| **Config/keys** | `backend/config.py` + `.env` | Add new settings fields |

### Instagram Graph API

**Portal:** https://developers.facebook.com/docs/instagram-api/getting-started  
**Docs:** https://developers.facebook.com/docs/instagram-api/reference/ig-user/media

1. Create a Meta app → add **Instagram Graph API** product
2. Connect an Instagram Business/Creator account to a Facebook Page
3. Generate a long-lived access token via Graph API Explorer
4. Add to `.env`:
   ```
   INSTAGRAM_ACCESS_TOKEN=your_token
   INSTAGRAM_USER_ID=your_ig_business_account_id
   ```

Fetches recent media captions from your connected business account, filtered by query keywords.

### Pinterest API v5

**Portal:** https://developers.pinterest.com/apps/  
**Docs:** https://developers.pinterest.com/docs/api/v5/#tag/search

1. Create a Pinterest app at the developer portal
2. Generate an access token with `pins:read` scope
3. Add to `.env`:
   ```
   PINTEREST_ACCESS_TOKEN=your_token
   ```

Uses the `/v5/search/pins` endpoint to find pins matching the query.

### SerpAPI — Google Search and Google Trends

**API key:** https://serpapi.com/manage-api-key

1. Create a SerpAPI account and copy your API key.
2. Add to `.env`:
   ```
   SERPAPI_API_KEY=your_api_key
   SERPAPI_GOOGLE_DOMAIN=google.com
   SERPAPI_TRENDS_GEO=
   SERPAPI_TRENDS_DATE=today 12-m
   ```

SerpAPI's `google` engine returns web results, while its `google_trends`
engine returns interest-over-time points. Both are normalized into the
SOCIALIQ acquisition records and participate in downstream trend analysis.

### X (Twitter) API — example stub

**Portal:** https://developer.x.com/en/portal/dashboard  
**Docs:** https://docs.x.com/x-api/posts/search/quickstart/recent-search

In `agents/data_acquisition/agent.py`, implement `_fetch_x()`:

```python
async def _fetch_x(self, query: str, entities: list[str]) -> list[dict]:
    import httpx
    headers = {"Authorization": f"Bearer {self.settings.x_bearer_token}"}
    params = {"query": query, "max_results": 20, "tweet.fields": "created_at,public_metrics"}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://api.x.com/2/tweets/search/recent",
            headers=headers, params=params,
        )
        # Map response to SOCIALIQ record format
```

### Telegram Bot API — example stub

**BotFather:** https://t.me/BotFather  
**Docs:** https://core.telegram.org/bots/api

In `agents/data_acquisition/agent.py`, implement `_fetch_telegram()`:

```python
async def _fetch_telegram(self, query: str, entities: list[str]) -> list[dict]:
    import httpx
    token = self.settings.telegram_bot_token
    # Use getUpdates or channel-specific methods
    url = f"https://api.telegram.org/bot{token}/getUpdates"
```

### OpenAI (LLM)

**Keys:** https://platform.openai.com/api-keys  
**Docs:** https://platform.openai.com/docs/api-reference/chat

Already connected in `agents/insight/agent.py`. Set in `.env`:
```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

---

## 3. Frontend Tool/Connector Controls

The UI **Tools & Connectors** panel (right sidebar) maps to:

| UI control | Backend field | Effect |
|------------|---------------|--------|
| Auto/Manual toggle | `tools.mode` | `"auto"` or `"manual"` |
| Agent toggles | `tools.enabled_agents` | Which agents run |
| Source toggles | `tools.enabled_sources` | Which data platforms to query |

Agent/source catalog is defined in:
- `backend/services/tools_registry.py`

Chat request schema:
- `backend/models/schemas.py` → `ToolConfig`, `ChatRequest`

---

## 4. Quick Reference — File Map

```
socialiq/
├── .env                          ← ALL API keys go here
├── backend/
│   ├── config.py                 ← Reads .env settings
│   ├── api/routes.py             ← REST endpoints
│   └── services/
│       ├── orchestrator.py       ← Pipeline coordinator
│       ├── tools_registry.py     ← Agent/source catalog
│       └── chat_store.py         ← Chat persistence
├── agents/
│   ├── master/planner.py         ← Intent, domain, workflow selection
│   ├── data_acquisition/agent.py ← ⭐ Connect social APIs HERE
│   └── insight/agent.py          ← ⭐ LLM integration HERE
├── workflows/n8n/
│   └── master_workflow.json      ← Import into n8n
└── docker/docker-compose.yml     ← Postgres, Redis, Neo4j, n8n
```

---

## 5. Running Everything

```bash
# Terminal 1 — Backend
cd socialiq
python run_backend.py

# Terminal 2 — Frontend
cd socialiq/frontend
npm run dev

# Terminal 3 — Infrastructure (optional)
docker compose -f docker/docker-compose.yml up -d
```

- Frontend: http://localhost:3000  
- API docs: http://localhost:8000/docs  
- n8n: http://localhost:5678  
- Neo4j browser: http://localhost:7474  
