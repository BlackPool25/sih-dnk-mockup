"""voice-pipeline API — Hindi STT/TTS/translate via the Sarvam AI cloud API."""

from __future__ import annotations

import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.sarvam import SarvamError, get_sarvam_client

MAX_TTS_CHARS = 400

app = FastAPI(title="voice-pipeline", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TTSRequest(BaseModel):
    text: str
    language: str = "hi"


class TranslateRequest(BaseModel):
    input: str
    source_language_code: str = "auto"
    target_language_code: str = "hi-IN"


def _elapsed_ms(start_ns: int) -> int:
    return int((time.monotonic_ns() - start_ns) // 1_000_000)


def _quality(transcript: str) -> dict[str, int | bool]:
    """Transcript-based quality gate: a single garbled word flags low confidence."""
    word_count = len(transcript.split())
    low_confidence = word_count < 2 or not transcript.strip()
    return {"word_count": word_count, "low_confidence": low_confidence}


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "provider": "sarvam"}


@app.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...), language_hint: str = Form("hi")
) -> dict[str, str | int | float | bool | None]:
    audio = await file.read()
    if not audio:
        raise HTTPException(status_code=400, detail="empty audio file")
    start_ns = time.monotonic_ns()
    try:
        result = get_sarvam_client().transcribe_full(audio, language="hi-IN")
    except SarvamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    transcript = str(result["transcript"])
    response: dict[str, str | int | float | bool | None] = {
        "transcript": transcript,
        "language": "hi-IN",
        "duration_ms": _elapsed_ms(start_ns),
        "provider": "sarvam",
        **_quality(transcript),
    }
    if result["language_probability"] is not None:
        response["language_probability"] = result["language_probability"]
    return response


@app.post("/tts")
def tts(body: TTSRequest) -> Response:
    if len(body.text) > MAX_TTS_CHARS:
        raise HTTPException(status_code=400, detail=f"text exceeds {MAX_TTS_CHARS} characters")
    try:
        wav = get_sarvam_client().synthesize(body.text, "hi-IN")
    except SarvamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return Response(content=wav, media_type="audio/wav")


@app.post("/translate")
def translate(body: TranslateRequest) -> dict[str, str]:
    try:
        translated = get_sarvam_client().translate(
            body.input, source=body.source_language_code, target=body.target_language_code
        )
    except SarvamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"translated_text": translated}
