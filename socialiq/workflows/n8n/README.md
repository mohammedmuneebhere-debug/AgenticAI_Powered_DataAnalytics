# n8n Workflows

Import `master_workflow.json` into n8n (http://localhost:5678) to orchestrate SOCIALIQ queries via webhook.

## X/Twitter recent-search workflow

`twitter_scraper_workflow.json` is an importable workflow that searches recent public X posts
through the X API v2 endpoint. It reads `X_BEARER_TOKEN` from the n8n container environment;
the token is not stored in the workflow JSON.

### Setup

1. Ensure `X_BEARER_TOKEN` is set in the project-root `.env`.
2. Restart n8n so Docker Compose passes the current value into the container:

   ```bash
   docker compose -f docker/docker-compose.yml up -d --force-recreate n8n
   ```

3. In n8n, choose **Workflows → Import from File** and select
   `workflows/n8n/twitter_scraper_workflow.json`.
4. Execute it once with a test request, then activate it if the response is correct.

Send a search request to the active webhook:

```bash
curl -X POST http://localhost:5678/webhook/socialiq/twitter-search ^
  -H "Content-Type: application/json" ^
  -d "{\"query\":\"\\\"data analytics\\\" -is:retweet lang:en\",\"max_results\":10}"
```

The `query` and `max_results` fields are optional. If omitted, the workflow searches for
`"AI" -is:retweet lang:en` and returns 10 posts. X API access level and rate limits still apply.

## Telegram updates workflow

`telegram_scraper_workflow.json` retrieves messages received by your Telegram bot through
the Bot API `getUpdates` endpoint. It reads `TELEGRAM_BOT_TOKEN` from the n8n container
environment and does not store the token in the workflow JSON.

### Setup and test

1. Add the bot to the target group or channel and grant the required permissions.
2. Ensure `TELEGRAM_BOT_TOKEN` is set in the project-root `.env`.
3. Restart n8n to load the current environment value:

   ```bash
   docker compose -f docker/docker-compose.yml up -d --force-recreate n8n
   ```

4. Import `workflows/n8n/telegram_scraper_workflow.json` into n8n.
5. Send a message to a chat the bot can access, then call the webhook:

   ```bash
   curl -X POST http://localhost:5678/webhook/socialiq/telegram-updates ^
     -H "Content-Type: application/json" ^
     -d "{\"query\":\"AI\",\"limit\":100}"
   ```

`query` is optional and performs a case-insensitive text filter. Telegram updates are
consumed by the Bot API, so repeated calls can return no messages after updates have been
acknowledged. This workflow does not scrape arbitrary public Telegram content; the bot must
be a member of the relevant chat/channel.

## Flow

```
Webhook → HTTP Request (FastAPI /api/v1/chat) → Respond
```

## Usage

```bash
curl -X POST http://localhost:5678/webhook/socialiq \
  -H "Content-Type: application/json" \
  -d '{"message": "Analyze coffee trends for winter product launch"}'
```

n8n handles branching, retries, scheduling, and multi-agent coordination. Heavy ML runs in Python services; n8n coordinates them.
