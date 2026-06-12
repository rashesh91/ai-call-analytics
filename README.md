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

## Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 8 GB | 16 GB |
| **CPU** | 4 cores | 8 cores |
| **Disk** | 20 GB free | 40 GB free |
| **OS** | Ubuntu 20.04 / RHEL 8 | Ubuntu 22.04 LTS |

> Mistral 7B runs on CPU — no GPU required. The model file is ~4 GB; Whisper `small` is ~500 MB.
> With 8 GB RAM, analysis of a single call takes 8–15 seconds. With 16 GB, it takes 3–6 seconds.

---

## Prerequisites

### Option A — Docker (recommended)

| Dependency | Minimum version | Install |
|------------|----------------|---------|
| **Docker Engine** | 24.0+ | `sudo apt install docker.io` |
| **Docker Compose** | v2.20+ | `sudo apt install docker-compose-plugin` |
| **curl** | any | `sudo apt install curl` |

Verify:
```bash
docker --version          # Docker version 24.x.x
docker compose version    # Docker Compose version v2.x.x
```

### Option B — Local / No Docker

| Dependency | Minimum version | Notes |
|------------|----------------|-------|
| **Python** | 3.10+ | `python3 --version` |
| **pip** | 23+ | `pip3 --version` |
| **MySQL** | 8.0+ or MariaDB 10.6+ | Must be running locally |
| **Ollama** | latest | Runs Mistral 7B locally |

Verify:
```bash
python3 --version          # Python 3.10.x or higher
mysql --version            # MySQL 8.x or MariaDB 10.6
ollama --version           # ollama version x.x.x
```

### Kubernetes (production)

| Dependency | Minimum version |
|------------|----------------|
| **kubectl** | 1.27+ |
| **Helm** | 3.12+ |
| **Kubernetes cluster** | 1.27+ |

---

## Installation

### Option A — Docker Compose (full stack, recommended)

```bash
# 1. Clone the repository
git clone https://github.com/rashesh91/ai-call-analytics.git
cd ai-call-analytics

# 2. Start all services (MySQL + Ollama + Whisper + Analytics)
docker compose up -d

# 3. Wait for Ollama to finish pulling Mistral 7B (~4 GB, first run only)
docker compose logs -f ollama
# You will see "success" when the model is ready

# 4. Wait for all services to pass health checks (~3–5 minutes first time)
docker compose ps   # all services should show "healthy"

# 5. Seed demo data (pre-computed — no AI processing wait needed)
pip3 install pymysql requests
MYSQL_HOST=localhost MYSQL_PORT=3307 python3 simulator/seed_local.py

# 6. Open the dashboard
open http://localhost:8080        # macOS
xdg-open http://localhost:8080   # Linux
```

**Environment variables** — override defaults in `docker-compose.yml`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MYSQL_HOST` | `mysql` | MySQL hostname |
| `MYSQL_PORT` | `3306` | MySQL port |
| `MYSQL_USER` | `root` | MySQL user |
| `MYSQL_PASSWORD` | `lintel@365` | MySQL password — **change in production** |
| `MYSQL_DATABASE` | `symphony` | Database name |
| `WHISPER_URL` | `http://whisper:8001` | Whisper service URL |
| `OLLAMA_URL` | `http://ollama:11434` | Ollama service URL |
| `OLLAMA_MODEL` | `mistral:7b` | LLM model name |
| `BATCH_INTERVAL_SECONDS` | `60` | Scan interval for unanalyzed calls |

---

### Option B — Local / No Docker (demo without Docker)

Use this path when Docker is not available or you want to connect to an existing MySQL.

```bash
# 1. Clone the repository
git clone https://github.com/rashesh91/ai-call-analytics.git
cd ai-call-analytics

# 2. Install Python dependencies
pip3 install -r analytics/requirements.txt --break-system-packages

# 3. Install Ollama and pull Mistral 7B (~4 GB download, one-time)
curl -fsSL https://ollama.com/install.sh | sh
ollama pull mistral:7b

# 4. Set up MySQL database
mysql -u root -p <<EOF
CREATE DATABASE IF NOT EXISTS symphony;
CREATE USER IF NOT EXISTS 'demo'@'localhost' IDENTIFIED BY 'demo123';
GRANT ALL PRIVILEGES ON symphony.* TO 'demo'@'localhost';
FLUSH PRIVILEGES;
EOF

# 5. Start the analytics service
export MYSQL_HOST=localhost MYSQL_PORT=3306 MYSQL_USER=demo
export MYSQL_PASSWORD=demo123 MYSQL_DATABASE=symphony
export OLLAMA_URL=http://localhost:11434

cd analytics && uvicorn app.main:app --host 0.0.0.0 --port 8080 &

# 6. Seed demo data (pre-computed — no Whisper/Ollama needed)
cd .. && pip3 install pymysql --break-system-packages
MYSQL_HOST=localhost MYSQL_PORT=3306 python3 simulator/seed_local.py

# 7. Open dashboard
open http://localhost:8080
```

> The seed script (`seed_local.py`) inserts pre-computed AI results directly — the
> dashboard is fully populated without Whisper or Ollama running.

---

### Verify Installation

```bash
# Service health (should show whisper + ollama status)
curl http://localhost:8080/health
# {"status":"ok","whisper":true,"ollama":true}

# Overall stats (confirms data is seeded)
curl http://localhost:8080/stats
# {"total_calls":272,"analyzed_calls":272,...}

# Dashboard responds
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/
# 200
```

---

## Quick Start (docker-compose)

```bash
# Start all services
docker compose up -d

# Wait for Ollama to pull Mistral 7B (~4 GB, first run only)
docker compose logs -f ollama

# Seed demo data
MYSQL_HOST=localhost MYSQL_PORT=3307 python3 simulator/seed_local.py

# Open dashboard
open http://localhost:8080
```

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
