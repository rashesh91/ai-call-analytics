# AI Call Analytics Platform

> **GenAI for VoIP** — Add AI intelligence to any FreeSWITCH / Asterisk IVR system.
> After every call, Whisper transcribes the recording and Mistral extracts: complaint
> category, customer sentiment, product model mentioned, resolution status, and a
> 2-sentence summary — stored back into your existing MySQL database.

## Real-World Use Case

A manufacturing company handles 200+ IVR calls per day across multiple languages
(English, Hindi, Gujarati, Tamil, Telugu). Managers were manually listening to random
call samples to understand complaint trends. After adding AI analytics:

- Manager opens dashboard every Monday morning
- Sees: "43% installation complaints this week, top region identified, sentiment improving"
- Flagged: "6 calls with frustrated sentiment on Friday — all about delayed delivery"
- Zero calls listened to manually

**Industries that benefit from this platform:**
- Consumer goods manufacturers (appliances, sanitaryware, electronics)
- Telecom service providers
- BFSI customer support centres
- Healthcare and insurance IVR systems
- Any business running a FreeSWITCH or Asterisk IVR

## Architecture

```
FreeSWITCH RECORD_STOP event
  → Existing IVR application (unchanged)
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

## Connect to Your Existing FreeSWITCH IVR

Add **one line** to your IVR application's hangup handler:

```python
# At the top of your IVR module:
from ivr_hook.analytics_webhook import fire_analysis

# In your channel_hangup_complete() method:
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

## Connect to Your Production MySQL Database

Run the migration on your existing IVR database:

```bash
mysql -u root -p <your_database> < migration/add_ai_columns.sql
```

Then set the `MYSQL_DATABASE` environment variable to your database name.
All existing tables and data remain untouched — the migration only adds new `ai_*` columns.

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
  --from-literal=mysql-user=<db-user> \
  --from-literal=mysql-password=<db-password>

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
| **MySQL** | Works with your existing IVR database |
| **Docker Compose** | Local development |
| **Helm + ArgoCD** | Kubernetes production deployment |

## Languages Supported

Whisper auto-detects: English, Hindi, Gujarati, Tamil, Telugu (and 90+ others).
Mistral understands transcripts in all major Indian languages.

## Interview Narrative

*"Our client's IVR system handles 200+ calls per day. Managers were manually listening
to random call samples — very inefficient. I added an AI layer: Whisper transcribes
each recording after hang-up, Mistral extracts complaint category, sentiment, and product
model mentioned, all stored back in the existing MySQL database. The manager now opens
a dashboard Monday morning and sees the full week's call intelligence: top categories,
sentiment trends, and an AI-generated summary. Zero manual listening required."*
