import httpx
import json
import logging
import re
from .config import settings

log = logging.getLogger("analyzer")

_http = httpx.AsyncClient(timeout=120.0)

SYSTEM_PROMPT = """You are an AI assistant that analyzes customer service call transcripts for a sanitaryware company (CERA India — makes bathroom fittings, taps, washbasins, toilets).

Transcripts may be in English, Hindi, Gujarati, Tamil, or Telugu. Understand all of them.

Extract the following and return ONLY valid JSON (no explanation, no markdown):
{
  "category": "<one of: product_issue, installation, delivery, warranty, billing, general_inquiry, other>",
  "sentiment": "<one of: frustrated, neutral, satisfied>",
  "model_mentioned": "<product model name if mentioned, or null>",
  "resolved": <true if issue was resolved on the call, false if escalated or unresolved>,
  "summary": "<2 sentences describing the call in English>"
}

Category definitions:
- product_issue: defective product, not working, leaking, quality complaint
- installation: difficulty installing, plumber visit request, installation guidance
- delivery: order not received, wrong item, delayed delivery
- warranty: asking about warranty, warranty claim
- billing: payment issue, invoice, refund
- general_inquiry: asking for product info, pricing, dealer location
- other: anything else"""


def _extract_json(text: str) -> dict:
    """Robustly extract JSON from LLM response that might have extra text."""
    text = text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return json.loads(text)


async def analyze_transcript(transcript: str) -> dict:
    """Send transcript to Ollama, return structured analysis dict."""
    if not transcript or len(transcript.strip()) < 10:
        return {
            "category": "other",
            "sentiment": "neutral",
            "model_mentioned": None,
            "resolved": False,
            "summary": "Call too short to analyze.",
            "confidence": 0.0,
        }

    payload = {
        "model": settings.ollama_model,
        "system": SYSTEM_PROMPT,
        "prompt": f"Transcript:\n{transcript[:3000]}",
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.1, "num_predict": 300},
    }

    resp = await _http.post(f"{settings.ollama_url}/api/generate", json=payload)
    resp.raise_for_status()
    raw = resp.json().get("response", "")

    try:
        result = _extract_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        log.warning("JSON parse failed: %s | raw: %s", e, raw[:200])
        result = {
            "category": "other",
            "sentiment": "neutral",
            "model_mentioned": None,
            "resolved": False,
            "summary": "Could not parse LLM response.",
        }

    # Normalise values
    valid_categories = {"product_issue", "installation", "delivery", "warranty", "billing", "general_inquiry", "other"}
    valid_sentiments = {"frustrated", "neutral", "satisfied"}
    result["category"] = result.get("category", "other") if result.get("category") in valid_categories else "other"
    result["sentiment"] = result.get("sentiment", "neutral") if result.get("sentiment") in valid_sentiments else "neutral"
    result["confidence"] = 0.9
    log.info("Analysis: category=%s sentiment=%s resolved=%s", result["category"], result["sentiment"], result.get("resolved"))
    return result
