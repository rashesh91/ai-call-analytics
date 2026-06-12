import httpx
import logging
import os
from .config import settings

log = logging.getLogger("transcriber")

_http = httpx.AsyncClient(timeout=120.0)


async def transcribe_file(audio_path: str) -> dict:
    """Send audio file to Whisper service, return {text, language}."""
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Recording not found: {audio_path}")

    with open(audio_path, "rb") as f:
        audio_bytes = f.read()

    filename = os.path.basename(audio_path)
    ext = os.path.splitext(filename)[1].lower()
    mime = "audio/wav" if ext == ".wav" else "audio/mpeg" if ext == ".mp3" else "audio/octet-stream"

    resp = await _http.post(
        f"{settings.whisper_url}/transcribe",
        files={"audio": (filename, audio_bytes, mime)},
    )
    resp.raise_for_status()
    data = resp.json()
    log.info("Transcribed %s: lang=%s, chars=%d", audio_path, data.get("language"), len(data.get("text", "")))
    return data
