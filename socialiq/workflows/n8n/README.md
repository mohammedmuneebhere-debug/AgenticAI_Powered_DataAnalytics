# n8n Workflows

Import `master_workflow.json` into n8n (http://localhost:5678) to orchestrate SOCIALIQ queries via webhook.

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
