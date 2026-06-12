import io
import logging
import os
import tempfile

from fastapi import FastAPI, File, UploadFile, HTTPException

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("whisper-service")

app = FastAPI(title="Whisper STT Service", version="1.0.0")

_model = None


def get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        model_size = os.getenv("WHISPER_MODEL", "small")
        log.info("Loading Whisper model: %s", model_size)
        _model = WhisperModel(model_size, device="cpu", compute_type="int8")
        log.info("Whisper model loaded")
    return _model


@app.on_event("startup")
async def startup():
    get_model()


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    suffix = os.path.splitext(audio.filename or "audio.wav")[1] or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_model()
        segments, info = model.transcribe(
            tmp_path,
            beam_size=3,
            language=None,       # auto-detect
            task="transcribe",
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        log.info("Transcribed: lang=%s prob=%.2f chars=%d", info.language, info.language_probability, len(text))
        return {
            "text": text,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration": round(info.duration, 2),
        }
    except Exception as e:
        log.error("Transcription failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _model is not None}
