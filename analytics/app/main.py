import logging
import asyncio
import os
import pathlib
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import httpx

from .config import settings
from .models import AnalyzeRequest, AnalyzeTextRequest
from . import database as db
from .transcriber import transcribe_file
from .analyzer import analyze_transcript

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("main")

_batch_task: asyncio.Task = None


async def _batch_worker():
    """Background worker: process unanalyzed calls every N seconds."""
    while True:
        try:
            calls = db.get_unanalyzed_calls(limit=10)
            for call in calls:
                await _process_call(call["unique_id"], call.get("file_path"))
        except Exception as e:
            log.error("Batch worker error: %s", e)
        await asyncio.sleep(settings.batch_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _batch_task
    try:
        db.run_migration()
        log.info("DB migration complete")
    except Exception as e:
        log.error("Migration failed (table may not exist yet): %s", e)
    _batch_task = asyncio.create_task(_batch_worker())
    yield
    _batch_task.cancel()


app = FastAPI(title="AI Call Analytics", version="1.0.0", lifespan=lifespan)


async def _process_call(unique_id: str, audio_path: str = None, transcript: str = None):
    try:
        if transcript is None:
            if not audio_path:
                call = db.get_call_by_uuid(unique_id)
                if call:
                    audio_path = call.get("file_path")
            if not audio_path:
                raise ValueError("No audio path and no transcript provided")
            result = await transcribe_file(audio_path)
            transcript = result.get("text", "")

        analysis = await analyze_transcript(transcript)
        db.save_analysis(unique_id, transcript, analysis)
        log.info("Processed call %s: %s / %s", unique_id, analysis["category"], analysis["sentiment"])
        return analysis
    except Exception as e:
        log.error("Failed to process call %s: %s", unique_id, e)
        db.save_error(unique_id, str(e))
        raise


@app.post("/analyze")
async def analyze_call(req: AnalyzeRequest, background: BackgroundTasks):
    """Trigger analysis of a call by unique_id (async, from IVR hook)."""
    background.add_task(_process_call, req.unique_id, req.audio_path)
    return {"status": "queued", "unique_id": req.unique_id}


@app.post("/analyze/text")
async def analyze_text(req: AnalyzeTextRequest):
    """Directly analyze a text transcript (for testing/simulator)."""
    analysis = await analyze_transcript(req.transcript)
    db.save_analysis(req.unique_id, req.transcript, analysis)
    return {"unique_id": req.unique_id, **analysis}


@app.post("/analyze/batch")
async def trigger_batch(background: BackgroundTasks):
    """Manually trigger batch processing of all unanalyzed calls."""
    calls = db.get_unanalyzed_calls(limit=100)
    for call in calls:
        background.add_task(_process_call, call["unique_id"], call.get("file_path"))
    return {"queued": len(calls)}


@app.get("/stats")
async def get_stats():
    """Overall dashboard stats."""
    return db.get_stats()


@app.get("/calls")
async def list_calls(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    category: str = Query(None),
):
    calls = db.get_calls_paginated(page=page, limit=limit, category=category)
    return {"page": page, "limit": limit, "calls": calls}


@app.get("/report/daily")
async def daily_report(date_str: str = Query(None, alias="date")):
    """Daily report with AI-generated narrative."""
    target = date_str or str(date.today())
    stats = db.get_daily_stats(target)

    if stats["analyzed_calls"] == 0:
        narrative = f"No analyzed calls found for {target}."
    else:
        top_cat = max(stats["categories"], key=stats["categories"].get) if stats["categories"] else "none"
        top_sent = max(stats["sentiments"], key=stats["sentiments"].get) if stats["sentiments"] else "none"
        try:
            narrative = await _generate_narrative(target, stats, top_cat, top_sent)
        except Exception:
            narrative = (
                f"On {target}: {stats['total_calls']} calls received. "
                f"Top category: {top_cat}. Overall sentiment: {top_sent}. "
                f"Average duration: {int(stats['avg_duration_seconds'])}s."
            )

    return {"date": target, **stats, "narrative": narrative}


@app.get("/report/weekly")
async def weekly_report(week_start: str = Query(None)):
    if week_start is None:
        today = date.today()
        week_start = str(today - timedelta(days=today.weekday()))
    week_end = str(date.fromisoformat(week_start) + timedelta(days=6))

    daily_trend = []
    total_calls = 0
    total_analyzed = 0
    agg_categories: dict = {}
    agg_sentiments: dict = {}

    for i in range(7):
        d = str(date.fromisoformat(week_start) + timedelta(days=i))
        day_stats = db.get_daily_stats(d)
        daily_trend.append({"date": d, "total": day_stats["total_calls"], "analyzed": day_stats["analyzed_calls"]})
        total_calls += day_stats["total_calls"]
        total_analyzed += day_stats["analyzed_calls"]
        for k, v in day_stats["categories"].items():
            agg_categories[k] = agg_categories.get(k, 0) + v
        for k, v in day_stats["sentiments"].items():
            agg_sentiments[k] = agg_sentiments.get(k, 0) + v

    top_cat = max(agg_categories, key=agg_categories.get) if agg_categories else "none"
    narrative = (
        f"Week {week_start} to {week_end}: {total_calls} total calls, "
        f"{total_analyzed} analyzed. Top category: {top_cat}. "
        f"Frustration rate: {agg_sentiments.get('frustrated', 0)} / {total_analyzed} analyzed calls."
    )

    return {
        "week_start": week_start,
        "week_end": week_end,
        "total_calls": total_calls,
        "analyzed_calls": total_analyzed,
        "categories": agg_categories,
        "sentiments": agg_sentiments,
        "daily_trend": daily_trend,
        "narrative": narrative,
    }


@app.get("/health")
async def health():
    whisper_ok = ollama_ok = False
    async with httpx.AsyncClient(timeout=3) as c:
        try:
            await c.get(f"{settings.whisper_url}/health")
            whisper_ok = True
        except Exception:
            pass
        try:
            await c.get(f"{settings.ollama_url}/api/tags")
            ollama_ok = True
        except Exception:
            pass
    return {"status": "ok", "whisper": whisper_ok, "ollama": ollama_ok}


async def _generate_narrative(date_str, stats, top_cat, top_sent) -> str:
    prompt = (
        f"Write a 3-sentence daily summary for a call center manager. "
        f"Date: {date_str}. Total calls: {stats['total_calls']}. "
        f"Analyzed: {stats['analyzed_calls']}. "
        f"Top category: {top_cat} ({stats['categories'].get(top_cat, 0)} calls). "
        f"Sentiment breakdown: {stats['sentiments']}. "
        f"Top language: {stats['top_language']}. "
        f"Avg call duration: {int(stats['avg_duration_seconds'])}s. "
        f"Be concise and professional."
    )
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 150},
    }
    async with httpx.AsyncClient(timeout=30) as c:
        resp = await c.post(f"{settings.ollama_url}/api/generate", json=payload)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()


import pathlib
_STATIC_DIR = os.environ.get(
    "STATIC_DIR",
    str(pathlib.Path(__file__).parent.parent.parent / "dashboard")
)
app.mount("/dashboard", StaticFiles(directory=_STATIC_DIR, html=True), name="static")


@app.get("/")
async def root():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
