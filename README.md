# AI Call Analytics Platform

> **GenAI for VoIP** — Add AI intelligence to any FreeSWITCH / Asterisk IVR system.
> After every call, Whisper transcribes the recording and Mistral extracts: complaint
> category, customer sentiment, product model mentioned, resolution status, and a
> 2-sentence summary — stored back into your existing MySQL database.

## Real-World Use Case

A sanitaryware manufacturer (CERA India) handles 200+ IVR calls per day across
5 languages (English, Hindi, Gujarati, Tamil, Telugu). Managers were manually listening
to random call samples to understand complaint trends. After adding AI analytics:

- Manager opens dashboard every Monday morning
- Sees: "43% installation complaints this week, Ahmedabad top area, sentiment improving"
- Flagged: "6 calls with frustrated sentiment on Friday — all about delayed delivery"
- Zero calls listened to manually

## Architecture

```
FreeSWITCH RECORD_STOP event
  → symphony-ivr ivr_1.py (existing, unchanged)
      → analytics_webhook.fire_analysis(call_uuid, rec_path)  [1 line added]
          ↓  fire-and-forget (does NOT block call)
  → analytics-service (FastAPI)
      → Whisper /transcribe  →  text transcript
      → Ollama/Mistral       →  {category, sentiment, model, resolved, summary}
      → MySQL UPDATE call_log SET ai_* = ...
  → Dashboard (http://localhost:8080)
      → Category breakdown pie chart
      → Sentiment distribution
      → Daily AI-generated narrative
      → Call log with AI summaries
```

## Quick Start (docker-compose)

```bash
# 1. Start all services (MySQL + Ollama + Whisper + Analytics)
docker-compose up -d

# 2. Wait for Ollama to pull Mistral 7B (~4GB first time)
docker-compose logs -f ollama

# 3. Seed demo data and run AI analysis
pip3 install pymysql requests
MYSQL_HOST=localhost MYSQL_PORT=3307 python3 simulator/seed_demo_data.py

# 4. Open dashboard
open http://localhost:8080
```

**System requirements:** 8GB RAM minimum (Mistral 7B runs on CPU)

## Connect to Your Existing symphony-ivr

Add **one line** to `ivr_1.py`:

```python
# At the top of ivr_1.py:
from ivr_hook.analytics_webhook import fire_analysis

# In channel_hangup_complete() method:
def channel_hangup_complete(self, event):
    ...
    fire_analysis(self.call_uuid, self.rec_file_path)  # ← add this line
```

Set environment variable:
```bash
export ANALYTICS_URL=http://analytics-service:8080
```

The hook is fire-and-forget — it runs in a background thread and does not block
the FreeSWITCH call flow.

## Connect to Production MySQL (symphony database)

For your existing symphony production database, run the migration:

```bash
mysql -u root -p symphony < migration/add_ai_columns.sql
```

Then update docker-compose.yml analytics service to point to your MySQL host
instead of the bundled container.

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Dashboard |
| `/stats` | GET | Overall stats for dashboard |
| `/analyze` | POST | Queue analysis for a call by UUID (from IVR hook) |
| `/analyze/text` | POST | Analyze transcript directly (for testing) |
| `/analyze/batch` | POST | Process all unanalyzed calls |
| `/calls` | GET | Paginated call list with AI analysis |
| `/report/daily?date=YYYY-MM-DD` | GET | Daily stats + AI narrative |
| `/report/weekly?week_start=YYYY-MM-DD` | GET | Weekly trend report |
| `/health` | GET | Health check (whisper + ollama status) |

## Kubernetes Deployment (Helm)

```bash
# Create secret
kubectl create secret generic ai-call-analytics-secret \
  --from-literal=mysql-user=root \
  --from-literal=mysql-password=lintel@365

# Install
helm install ai-call-analytics ./helm \
  --set analytics.env.MYSQL_HOST=your-mysql-host \
  --set ingress.host=ai-analytics.your-domain.com
```

## Stack

| Component | Purpose |
|-----------|---------|
| **FastAPI** | Analytics API + dashboard server |
| **faster-whisper** | Speech-to-text (CPU, multilingual) |
| **Ollama + Mistral 7B** | LLM analysis (runs locally, no OpenAI cost) |
| **MySQL** | Same database as symphony-ivr |
| **Docker Compose** | Local development |
| **Helm + ArgoCD** | Kubernetes production deployment |

## Languages Supported

Whisper auto-detects: English, Hindi, Gujarati, Tamil, Telugu (and 90+ others).
Mistral understands all Indian languages in transcripts.

## Interview Narrative

*"We had 200+ calls per day at the client's IVR system. Managers were manually listening
to random call samples — very inefficient. I added an AI layer: Whisper transcribes
each recording after hang-up, Mistral extracts complaint category, sentiment, and product
model mentioned, all stored back in the existing MySQL database. The manager now opens
a dashboard Monday morning and sees the full week's call intelligence: top categories,
sentiment trends, and an AI-generated summary. Zero manual listening required."*
