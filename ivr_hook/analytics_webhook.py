"""
Drop-in analytics hook for symphony-ivr-python3.11.

Usage — add ONE line to ivr_1.py channel_hangup_complete():

    from ivr_hook.analytics_webhook import fire_analysis
    ...
    def channel_hangup_complete(self, event):
        ...
        fire_analysis(self.call_uuid, self.rec_file_path)   # <-- add this line

That's it. Fire-and-forget: does NOT block the call flow.
"""

import threading
import requests
import logging
import os

log = logging.getLogger("analytics_webhook")

ANALYTICS_URL = os.getenv("ANALYTICS_URL", "http://localhost:8080")


def fire_analysis(call_uuid: str, rec_file_path: str = None):
    """
    Post call UUID to analytics service in a background thread.
    Non-blocking — returns immediately.

    Args:
        call_uuid:     FreeSWITCH call UUID (self.call_uuid)
        rec_file_path: Path to the final recording file (self.rec_file_path)
                       e.g. /opt/symphony/recording/20250115/1234567890/
    """
    def _post():
        try:
            payload = {"unique_id": call_uuid}
            if rec_file_path:
                # Find the main recording file in the directory
                audio_path = _find_recording(rec_file_path)
                if audio_path:
                    payload["audio_path"] = audio_path
            resp = requests.post(
                f"{ANALYTICS_URL}/analyze",
                json=payload,
                timeout=5,
            )
            if resp.ok:
                log.info("Queued analysis for call %s", call_uuid)
            else:
                log.warning("Analytics service returned %s for %s", resp.status_code, call_uuid)
        except Exception as e:
            log.error("Failed to queue analysis for %s: %s", call_uuid, e)

    t = threading.Thread(target=_post, daemon=True)
    t.start()


def _find_recording(rec_dir: str) -> str:
    """Find the primary recording WAV file in the recording directory."""
    if not rec_dir or not os.path.exists(rec_dir):
        return None

    # symphony-ivr records into a directory; look for the main recording
    # (not name.wav, address.wav etc — look for a file named by the caller number or UUID)
    for fname in os.listdir(rec_dir):
        if fname.endswith(".wav") and fname not in ("name.wav", "address.wav", "area.wav", "model.wav"):
            return os.path.join(rec_dir, fname)

    # fallback: any wav file
    for fname in os.listdir(rec_dir):
        if fname.endswith(".wav"):
            return os.path.join(rec_dir, fname)

    return None
