"""GET /guidance/signup — explicit Hindi toggle, per-field Sarvam hints.

Source: validation-engine/data/02-dnk-documents/onboarding/onboarding-guide.md
§1–§2 (8 steps), complete-flow §5A/5C. All mocked, never live-claimed.
Hinglish simple_words are class-5 level (short, spoken Hindi).
"""

from __future__ import annotations

import io
import math
import os
import struct
import wave
from typing import Final

import httpx
from fastapi import APIRouter, Body, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.sarvam import tts_url_for_field

router = APIRouter(prefix="/guidance", tags=["guidance"])

# ---------------------------------------------------------------------------
# Field registry — upfront order PAN→IEC→AD→ICEGATE→bank, then GSTIN/Udyam/RCMC “बाद में”
# Source: onboarding-guide.md §1–§2, complete-flow §5C minimal set
# ---------------------------------------------------------------------------

_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    {"pan", "iec", "ad_code", "icegate", "bank", "gstin", "udyam", "rcmc"}
)

# Canonical ordering for upfront vs skippable grouping
_UPFRONT_ORDER: Final[list[str]] = ["pan", "iec", "ad_code", "icegate", "bank"]
_SKIPPABLE_FIELDS: Final[frozenset[str]] = frozenset({"gstin", "udyam", "rcmc"})

# Normalise aliases (user typos / alternate spellings) before Levenshtein
_ALIASES: Final[dict[str, str]] = {
    "adcode": "ad_code",
    "ad-code": "ad_code",
    "ad": "ad_code",
    "pan_card": "pan",
    "iec_code": "iec",
    "iecc": "iec",
    "icgate": "icegate",
    "ice_gate": "icegate",
    "bank_account": "bank",
    "bankaccount": "bank",
    "gst": "gstin",
    "gstn": "gstin",
    "udyam_reg": "udyam",
    "rcms": "rcmc",
    "rcmc_code": "rcmc",
}


class FieldMeta(BaseModel):
    field: str
    simple_words: str
    hint: str
    required: bool
    skippable: bool
    source: str = "onboarding-guide.md §2"


# Hinglish — class-5 spoken, sourced from onboarding-guide.md §2 per field
_FIELD_META: Final[dict[str, FieldMeta]] = {
    "pan": FieldMeta(
        field="pan",
        simple_words="PAN कार्ड — 10 अक्षर (ABCDE1234F जैसा)",
        hint="PAN से IEC बनता है — पहले यही लगता है [guide §2 Step1]",
        required=True,
        skippable=False,
    ),
    "iec": FieldMeta(
        field="iec",
        simple_words="बाहर सामान भेजने का लाइसेंस (IEC) 10 अंक",
        hint="DGFT से बनता है, ₹500 फीस, OTP से तुरंत [guide §2 Step1]",
        required=True,
        skippable=False,
    ),
    "ad_code": FieldMeta(
        field="ad_code",
        simple_words="बैंक का 14 नंबर कोड बगल-बगल",
        hint="बैंक देता है, ICEGATE पर रजिस्टर होता है — incentive के लिए जरूरी [guide §2 Step3]",
        required=True,
        skippable=False,
    ),
    "icegate": FieldMeta(
        field="icegate",
        simple_words="कस्टम का ऑनलाइन खाता",
        hint="icegate.gov.in पर बनता है, बैंक खाता DNK site code से लिंक [guide §2 Step4]",
        required=True,
        skippable=False,
    ),
    "bank": FieldMeta(
        field="bank",
        simple_words="₹1 भेजकर खाता चेक",
        hint="फर्म के नाम का खाता — IEC और refund यहीं आता है [guide §2 Step2]",
        required=True,
        skippable=False,
    ),
    "gstin": FieldMeta(
        field="gstin",
        simple_words="GST नंबर — बाद में",
        hint="बाद में — अभी skip कर सकते हैं [guide §4 honesty: GSTIN not mandatory]",
        required=False,
        skippable=True,
    ),
    "udyam": FieldMeta(
        field="udyam",
        simple_words="छोटा उद्योग सर्टिफिकेट — बाद में",
        hint="बाद में — सिर्फ सरकारी योजना लेनी हो तो [guide §2 Step7]",
        required=False,
        skippable=True,
    ),
    "rcmc": FieldMeta(
        field="rcmc",
        simple_words="EPCH सदस्यता (RCMC) — बाद में",
        hint="बाद में — हस्तशिल्प निर्यात योजना के लिए [guide §2 Step7]",
        required=False,
        skippable=True,
    ),
}

# English slug fallback when hindi_help=false
_ENGLISH_FALLBACK: Final[dict[str, str]] = {
    "pan": "PAN card — 10 characters",
    "iec": "export licence (IEC) — 10 digits",
    "ad_code": "bank AD Code — 14 digits",
    "icegate": "customs online account (ICEGATE)",
    "bank": "bank account verification (Rs 1 check)",
    "gstin": "GSTIN — later (skippable)",
    "udyam": "Udyam certificate — later (skippable)",
    "rcmc": "RCMC membership — later (skippable)",
}


def _normalize_field(raw: str) -> str:
    s = raw.strip().lower().replace(" ", "_").replace("-", "_")
    # collapse double underscores
    while "__" in s:
        s = s.replace("__", "_")
    s = s.strip("_")
    if s in _ALIASES:
        return _ALIASES[s]
    # try alias without underscores
    compact = s.replace("_", "")
    if compact in _ALIASES:
        return _ALIASES[compact]
    if s in _ALLOWED_FIELDS:
        return s
    if compact in _ALLOWED_FIELDS:
        return compact
    return s


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * lb
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[lb]


def resolve_field(raw: str) -> str | None:
    """Typo-tolerant field resolution — alias → exact → Levenshtein ≤2."""
    norm = _normalize_field(raw)
    if norm in _ALLOWED_FIELDS:
        return norm
    # Levenshtein fallback (threshold 2)
    best: str | None = None
    best_dist = 999
    for cand in _ALLOWED_FIELDS:
        d = _levenshtein(norm, cand)
        if d < best_dist:
            best_dist = d
            best = cand
    if best is not None and best_dist <= 2:
        return best
    # also try without underscores for iec-like typos
    for cand in _ALLOWED_FIELDS:
        d = _levenshtein(norm.replace("_", ""), cand.replace("_", ""))
        if d < best_dist:
            best_dist = d
            best = cand
    if best is not None and best_dist <= 2:
        return best
    return None


class GuidanceResponse(BaseModel):
    field: str
    simple_words: str
    hint: str
    side_by_side: None = None
    tts_url: str | None = None
    required: bool
    skippable: bool
    verification_mode: str = "mock"
    mocked: bool = True
    hindi_help: bool
    source: str = "onboarding-guide.md §2"
    upfront_order: list[str] = _UPFRONT_ORDER


@router.get("/signup")
async def get_signup_guidance(
    field: str = Query(..., description="one of pan|iec|ad_code|icegate|bank|gstin|udyam|rcmc (typo-tolerant)"),
    hindi_help: bool = Query(..., description="explicit toggle: true=Hindi, false=English (no auto-detect)"),
) -> GuidanceResponse:
    resolved = resolve_field(field)
    if resolved is None:
        # still return 200 with best-effort — surface closest or pan
        resolved = "pan"
    meta = _FIELD_META[resolved]
    if hindi_help:
        # Every field gets a Sarvam mock tts_url when Hindi is on
        tts = tts_url_for_field(resolved, meta.simple_words)
        return GuidanceResponse(
            field=resolved,
            simple_words=meta.simple_words,
            hint=meta.hint,
            side_by_side=None,
            tts_url=tts,
            required=meta.required,
            skippable=meta.skippable,
            verification_mode="mock",
            mocked=True,
            hindi_help=True,
            source=meta.source,
            upfront_order=_UPFRONT_ORDER,
        )
    else:
        eng = _ENGLISH_FALLBACK.get(resolved, resolved)
        return GuidanceResponse(
            field=resolved,
            simple_words=eng,
            hint=eng,
            side_by_side=None,
            tts_url=None,
            required=meta.required,
            skippable=meta.skippable,
            verification_mode="mock",
            mocked=True,
            hindi_help=False,
            source=meta.source,
            upfront_order=_UPFRONT_ORDER,
        )


# ---------------------------------------------------------------------------
# Public TTS fallback — POST /guidance/tts (no auth, always audible)
# Proxies to voice-pipeline /tts or Sarvam live; on 401/missing key returns
# a generated WAV beep so signup Play is never silent.
# ---------------------------------------------------------------------------


class TTSBody(BaseModel):
    text: str = ""
    language: str = "hi"
    field: str | None = None


def _mock_wav_bytes(text: str = "beep") -> bytes:
    """Generate a short audible WAV beep (guaranteed audible offline).

    Two-tone pattern 880Hz(0.35s) + silence(0.05s) + 660Hz(0.3s) + fade,
    16kHz mono 16-bit PCM. Duration ~0.7s, ~22kB, loud enough on any speaker.
    """
    sr = 16000
    dur = 0.70
    samples = int(sr * dur)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for i in range(samples):
            t = i / sr
            if t < 0.35:
                f = 880.0
                if t < 0.02:
                    env = t / 0.02
                elif t < 0.33:
                    env = 1.0
                else:
                    env = (0.35 - t) / 0.02
            elif t < 0.40:
                f = 0.0
                env = 0.0
            else:
                f = 660.0
                if t < 0.42:
                    env = (t - 0.40) / 0.02
                elif t < 0.68:
                    env = 1.0
                else:
                    env = (0.70 - t) / 0.02
            if f == 0.0 or env <= 0:
                v = 0
            else:
                v = int(14000 * env * math.sin(2 * math.pi * f * t))
            w.writeframes(struct.pack("<h", int(max(-32767, min(32767, v)))))
    return buf.getvalue()


@router.post("/tts")
async def guidance_tts(body: dict = Body(...)) -> Response:  # type: ignore[no-untyped-def]
    """Public TTS — no auth required. Proxies to voice-pipeline, falls back to mock WAV."""
    raw_text = str(body.get("text") or body.get("input") or body.get("hint") or "").strip()
    language = str(body.get("language") or "hi").strip().lower()
    # Normalize language code for downstream
    lang_code = "hi-IN" if language.startswith("hi") else "en-IN"
    # Ensure non-empty text so downstream never rejects with 400
    text = raw_text if raw_text else "नमस्ते"
    # Truncate to voice-pipeline limit
    if len(text) > 400:
        text = text[:400]

    # Try live voice-pipeline if reachable (internal docker dns)
    voice_url = os.getenv("VOICE_PIPELINE_URL", "http://voice-pipeline:8000")
    # In docker compose, settings may not be loaded here; also try storage.config
    try:
        from storage.config import settings as _s

        voice_url = _s.VOICE_PIPELINE_URL
    except Exception:
        pass

    # Attempt live TTS via voice-pipeline
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                f"{voice_url.rstrip('/')}/tts",
                json={"text": text, "language": lang_code.split("-")[0]},
            )
            if resp.status_code < 400 and resp.content and len(resp.content) > 200:
                # voice-pipeline returns audio/wav bytes
                ctype = resp.headers.get("content-type", "audio/wav")
                return Response(content=resp.content, media_type=ctype)
    except Exception:
        pass

    # Try direct Sarvam live call if key present
    try:
        sarvam_key = os.getenv("SARVAM_API_KEY", "")
        if sarvam_key:
            import base64 as _b64

            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.post(
                    "https://api.sarvam.ai/text-to-speech",
                    headers={"api-subscription-key": sarvam_key},
                    json={
                        "text": text,
                        "model": "bulbul:v2",
                        "target_language_code": lang_code,
                        "speaker": "anushka",
                    },
                )
                if r.status_code < 400:
                    data = r.json()
                    audios = data.get("audios") or []
                    if audios and isinstance(audios[0], str):
                        wav_bytes = _b64.b64decode(audios[0])
                        if len(wav_bytes) > 200:
                            return Response(content=wav_bytes, media_type="audio/wav")
                    # Also handle audio_url case
                    url = data.get("audio_url") or data.get("url")
                    if isinstance(url, str) and url.startswith("http"):
                        async with httpx.AsyncClient(timeout=8.0) as c2:
                            r2 = await c2.get(url)
                            if r2.status_code < 400 and len(r2.content) > 200:
                                return Response(content=r2.content, media_type="audio/wav")
    except Exception:
        pass

    # Fallback: generated beep WAV (always audible, no auth, no network)
    wav = _mock_wav_bytes(text)
    return Response(content=wav, media_type="audio/wav", headers={"X-Mock-TTS": "beep-fallback", "X-Text-Len": str(len(text))})
