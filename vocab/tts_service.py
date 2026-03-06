"""
TTS Service — Google Cloud Text-to-Speech → Azure Blob Storage → DB

Uses Google TTS REST API (API Key auth, no service account needed).
Uploads MP3 to Azure Blob "audio" container and saves URL to WordEntry.
"""

import io
import logging
import time
from typing import Optional

import requests
from azure.storage.blob import BlobServiceClient, ContentSettings
from django.conf import settings

logger = logging.getLogger(__name__)

# ── Voice configuration ──────────────────────────────────────
# Default voices (used by batch_generate when no voice is specified)
VOICES = {
    "en": {
        "us": {"language_code": "en-US", "name": "en-US-Neural2-J", "label": "US"},
        "uk": {"language_code": "en-GB", "name": "en-GB-Neural2-B", "label": "UK"},
    },
    "jp": {
        "default": {"language_code": "ja-JP", "name": "ja-JP-Neural2-B", "label": "JP"},
    },
}

# All available voice options for admin UI picker
AVAILABLE_VOICES = {
    "en-US": [
        {"name": "en-US-Studio-Q",   "gender": "Male",   "quality": "Studio",  "note": "⭐ Xịn nhất — giọng studio chuyên nghiệp, tự nhiên như người thật"},
        {"name": "en-US-Studio-O",   "gender": "Female", "quality": "Studio",  "note": "⭐ Xịn nhất — nữ studio, phát âm rõ ràng"},
        {"name": "en-US-Neural2-J",  "gender": "Male",   "quality": "Neural2", "note": "Rất tốt — neural AI, giọng nam tự nhiên"},
        {"name": "en-US-Neural2-H",  "gender": "Female", "quality": "Neural2", "note": "Rất tốt — neural AI, giọng nữ"},
        {"name": "en-US-Neural2-D",  "gender": "Male",   "quality": "Neural2", "note": "Tốt — nam trầm, phù hợp từ điển"},
        {"name": "en-US-Neural2-A",  "gender": "Male",   "quality": "Neural2", "note": "Tốt — nam nhẹ nhàng"},
        {"name": "en-US-Wavenet-D",  "gender": "Male",   "quality": "Wavenet", "note": "Khá — wavenet nam"},
        {"name": "en-US-Wavenet-C",  "gender": "Female", "quality": "Wavenet", "note": "Khá — wavenet nữ"},
    ],
    "en-GB": [
        {"name": "en-GB-Studio-B",   "gender": "Male",   "quality": "Studio",  "note": "⭐ Xịn nhất — giọng Anh studio, RP chuẩn"},
        {"name": "en-GB-Studio-C",   "gender": "Female", "quality": "Studio",  "note": "⭐ Xịn nhất — nữ Anh studio"},
        {"name": "en-GB-Neural2-B",  "gender": "Male",   "quality": "Neural2", "note": "Rất tốt — neural nam Anh"},
        {"name": "en-GB-Neural2-A",  "gender": "Female", "quality": "Neural2", "note": "Rất tốt — neural nữ Anh"},
        {"name": "en-GB-Wavenet-B",  "gender": "Male",   "quality": "Wavenet", "note": "Khá — wavenet nam Anh"},
    ],
    "ja-JP": [
        {"name": "ja-JP-Neural2-B",  "gender": "Female", "quality": "Neural2", "note": "Rất tốt — phát âm chuẩn"},
        {"name": "ja-JP-Neural2-C",  "gender": "Male",   "quality": "Neural2", "note": "Rất tốt — giọng nam"},
        {"name": "ja-JP-Neural2-D",  "gender": "Male",   "quality": "Neural2", "note": "Tốt — nam nhẹ nhàng"},
        {"name": "ja-JP-Wavenet-B",  "gender": "Female", "quality": "Wavenet", "note": "Khá — wavenet nữ"},
    ],
}

DEFAULT_SPEAKING_RATE = 0.92  # Slightly slow for dictionary clarity

TTS_API_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"


def synthesize_word(
    word: str,
    language_code: str,
    voice_name: str,
    speaking_rate: float = DEFAULT_SPEAKING_RATE,
) -> bytes:
    """
    Call Google Cloud TTS REST API to synthesize a word.
    Returns raw MP3 bytes.
    """
    api_key = getattr(settings, "GOOGLE_TTS_API_KEY", "")
    if not api_key:
        raise ValueError("GOOGLE_TTS_API_KEY is not configured in settings/.env")

    payload = {
        "input": {"text": word},
        "voice": {
            "languageCode": language_code,
            "name": voice_name,
        },
        "audioConfig": {
            "audioEncoding": "MP3",
            "speakingRate": speaking_rate,
            "pitch": 0.0,
        },
    }

    resp = requests.post(
        f"{TTS_API_URL}?key={api_key}",
        json=payload,
        timeout=30,
    )

    if resp.status_code != 200:
        error_detail = resp.text[:500]
        raise RuntimeError(
            f"Google TTS API error {resp.status_code}: {error_detail}"
        )

    import base64
    audio_content = resp.json().get("audioContent")
    if not audio_content:
        raise RuntimeError("Google TTS returned empty audioContent")

    return base64.b64decode(audio_content)


def upload_to_azure(audio_bytes: bytes, blob_path: str) -> str:
    """
    Upload MP3 bytes to Azure Blob Storage (audio container).
    Returns the public URL.
    """
    account_name = settings.AZURE_ACCOUNT_NAME
    account_key = settings.AZURE_ACCOUNT_KEY
    container = getattr(settings, "AZURE_AUDIO_CONTAINER", settings.AZURE_CONTAINER)

    if not account_name or not account_key:
        raise ValueError("Azure storage credentials not configured")

    conn_str = (
        f"DefaultEndpointsProtocol=https;"
        f"AccountName={account_name};"
        f"AccountKey={account_key};"
        f"EndpointSuffix=core.windows.net"
    )

    blob_service = BlobServiceClient.from_connection_string(conn_str)
    blob_client = blob_service.get_blob_client(container=container, blob=blob_path)

    content_settings = ContentSettings(content_type="audio/mpeg")

    blob_client.upload_blob(
        io.BytesIO(audio_bytes),
        overwrite=True,
        content_settings=content_settings,
    )

    url = f"https://{account_name}.blob.core.windows.net/{container}/{blob_path}"
    return url


def generate_audio_for_entry(
    entry_id: int,
    force: bool = False,
) -> dict:
    """
    Generate TTS audio for a single WordEntry.
    Returns dict with results: {entry_id, word, audio_us, audio_uk, status}
    """
    from vocab.models import WordEntry

    entry = WordEntry.objects.select_related("vocab").get(id=entry_id)
    word = entry.vocab.word
    lang = entry.vocab.language  # 'en' or 'jp'
    results = {"entry_id": entry_id, "word": word, "generated": []}

    voices = VOICES.get(lang, VOICES.get("en", {}))

    for accent, voice_cfg in voices.items():
        # Determine which field to update
        if lang == "en":
            field = f"audio_{accent}"  # audio_us or audio_uk
        else:
            field = "audio_us"  # For Japanese, store in audio_us

        current_value = getattr(entry, field, "")
        if current_value and not force:
            results["generated"].append(
                {"accent": accent, "status": "skipped", "url": current_value}
            )
            continue

        try:
            # Synthesize
            audio_bytes = synthesize_word(
                word, voice_cfg["language_code"], voice_cfg["name"]
            )

            # Upload to Azure
            safe_word = word.replace(" ", "_").replace("/", "_").replace("\\", "_")
            blob_path = f"tts/{lang}/{accent}/{safe_word}.mp3"
            url = upload_to_azure(audio_bytes, blob_path)

            # Update DB
            setattr(entry, field, url)
            entry.save(update_fields=[field])

            results["generated"].append(
                {"accent": accent, "status": "success", "url": url}
            )
            logger.info(f"TTS OK: {word} ({accent}) → {url}")

        except Exception as e:
            results["generated"].append(
                {"accent": accent, "status": "error", "error": str(e)}
            )
            logger.error(f"TTS FAIL: {word} ({accent}): {e}")

    return results


# ── In-memory progress tracking for admin UI ─────────────────
_batch_progress = {
    "running": False,
    "total": 0,
    "done": 0,
    "success": 0,
    "errors": 0,
    "current_word": "",
    "error_list": [],
}


def get_batch_progress() -> dict:
    return dict(_batch_progress)


def batch_generate(
    language: str = "en",
    limit: int = 50,
    force: bool = False,
) -> dict:
    """
    Batch generate TTS for WordEntries missing audio.
    Uses in-memory progress tracking for admin UI.
    """
    from vocab.models import WordEntry, Vocabulary
    from django.db.models import Q

    global _batch_progress
    if _batch_progress["running"]:
        return {"error": "Batch already running"}

    # Find entries needing audio
    qs = WordEntry.objects.filter(vocab__language=language).select_related("vocab")

    if not force:
        if language == "en":
            qs = qs.filter(Q(audio_us="") | Q(audio_uk=""))
        else:
            qs = qs.filter(audio_us="")

    entries = list(qs[:limit])

    _batch_progress.update({
        "running": True,
        "total": len(entries),
        "done": 0,
        "success": 0,
        "errors": 0,
        "current_word": "",
        "error_list": [],
    })

    try:
        for entry in entries:
            _batch_progress["current_word"] = entry.vocab.word

            result = generate_audio_for_entry(entry.id, force=force)

            has_error = any(
                g["status"] == "error" for g in result.get("generated", [])
            )
            if has_error:
                _batch_progress["errors"] += 1
                for g in result.get("generated", []):
                    if g["status"] == "error":
                        _batch_progress["error_list"].append(
                            f"{entry.vocab.word} ({g['accent']}): {g.get('error', '')}"
                        )
            else:
                _batch_progress["success"] += 1

            _batch_progress["done"] += 1

            # Rate limiting: ~5 requests/sec to stay within Google quotas
            time.sleep(0.3)

    finally:
        _batch_progress["running"] = False
        _batch_progress["current_word"] = ""

    return {
        "total": _batch_progress["total"],
        "success": _batch_progress["success"],
        "errors": _batch_progress["errors"],
        "error_list": _batch_progress["error_list"][:20],
    }
