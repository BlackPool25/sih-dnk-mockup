"""voice-pipeline API — Hindi STT/TTS/translate via the Sarvam AI cloud API."""

from __future__ import annotations

import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from app.sarvam import SarvamClient, SarvamError, get_sarvam_client

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


class TranslateTextItem(BaseModel):
    key: str
    text: str
    kind: str = "transliterate"  # "translate" | "transliterate"


class TranslateTextRequest(BaseModel):
    items: list[TranslateTextItem]


class TranslatedItem(BaseModel):
    key: str
    english: str


class TranslateTextResponse(BaseModel):
    items: list[TranslatedItem]


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


def _translate_item(client: SarvamClient, item: TranslateTextItem) -> str:
    """Translate/transliterate ONE item to English (target en-IN)."""
    return client.translate(
        item.text,
        target="en-IN",
        enable_indic_transliteration=(item.kind == "transliterate"),
    )


@app.post("/translate/text")
def translate_text(body: TranslateTextRequest) -> TranslateTextResponse:
    """Batch translate|transliterate free-text items to English in ONE mayura call.

    Items are newline-joined into a single upstream request; the response is
    split back per item. If the upstream collapses lines, each item is retried
    individually so no item is ever lost.
    """
    if not body.items:
        raise HTTPException(status_code=400, detail="items must not be empty")
    keys = [item.key for item in body.items]
    if len(keys) != len(set(keys)):
        raise HTTPException(status_code=400, detail="duplicate item key")
    for item in body.items:
        if not item.text.strip():
            raise HTTPException(status_code=400, detail=f"empty text for item '{item.key}'")

    client = get_sarvam_client()
    try:
        if len(body.items) == 1:
            english = _translate_item(client, body.items[0])
            return TranslateTextResponse(
                items=[TranslatedItem(key=body.items[0].key, english=english)]
            )

        joined = "\n".join(item.text for item in body.items)
        any_transliterate = any(item.kind == "transliterate" for item in body.items)
        translated = client.translate(
            joined,
            target="en-IN",
            enable_indic_transliteration=any_transliterate,
        )
        parts = translated.split("\n")
        if len(parts) == len(body.items):
            return TranslateTextResponse(
                items=[
                    TranslatedItem(key=item.key, english=part)
                    for item, part in zip(body.items, parts, strict=True)
                ]
            )
        return TranslateTextResponse(
            items=[
                TranslatedItem(key=item.key, english=_translate_item(client, item))
                for item in body.items
            ]
        )
    except SarvamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
