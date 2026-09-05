# n8n workflow test queries

Use these requests after importing and activating the corresponding workflow.

## Master workflow

```powershell
$body = '{"message":"Why is BTC volatile today?"}'
Invoke-RestMethod -Uri "http://localhost:5678/webhook/socialiq" -Method Post -ContentType "application/json" -Body $body
```

## NewsAPI search

```powershell
$body = '{"query":"artificial intelligence","page_size":10,"language":"en","sort_by":"relevancy"}'
Invoke-RestMethod -Uri "http://localhost:5678/webhook/socialiq/news-search" -Method Post -ContentType "application/json" -Body $body
```

## X/Twitter search

```powershell
$body = '{"query":"AI","max_results":10}'
Invoke-RestMethod -Uri "http://localhost:5678/webhook/socialiq/twitter-search" -Method Post -ContentType "application/json" -Body $body
```

## Telegram updates

```powershell
$body = '{"query":"AI","limit":100}'
Invoke-RestMethod -Uri "http://localhost:5678/webhook/socialiq/telegram-updates" -Method Post -ContentType "application/json" -Body $body
```
