import logging
import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from typing import Optional

import mlx.core as mx
import mlx_whisper
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from mlx_whisper.load_models import load_model
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice-pipeline")

MODEL_NAME = "mlx-community/whisper-large-v3-turbo"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing voice-pipeline...")
    default_dev = mx.default_device()
    metal_avail = mx.metal.is_available()
    logger.info(f"MLX Device: {default_dev}, Metal Available: {metal_avail}")

    try:
        start = time.perf_counter()
        logger.info(f"Loading Whisper model '{MODEL_NAME}' at startup...")
        _ = load_model(MODEL_NAME)
        elapsed = time.perf_counter() - start
        logger.info(f"Whisper model '{MODEL_NAME}' loaded successfully in {elapsed:.4f}s.")
    except Exception as e:
        logger.critical(f"FATAL: Failed to load Whisper model at startup: {e}", exc_info=True)
        raise RuntimeError(f"Startup model load failed: {e}") from e

    yield

    logger.info("Shutting down voice-pipeline...")


app = FastAPI(title="voice-pipeline", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TranscribeResponse(BaseModel):
    text: str
    detected_language: str
    duration_seconds: float


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    file: UploadFile = File(...),
    language_hint: Optional[str] = Form(None),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Audio file must have a valid filename.")

    suffix = os.path.splitext(file.filename)[1].lower()
    if not suffix:
        suffix = ".wav"

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = tmp.name
            shutil.copyfileobj(file.file, tmp)

        file_size = os.path.getsize(temp_path)
        if file_size == 0:
            raise HTTPException(status_code=400, detail="Uploaded audio file is empty (0 bytes).")

        transcribe_kwargs = {
            "path_or_hf_repo": MODEL_NAME,
            "verbose": False,
        }
        if language_hint and language_hint.strip():
            transcribe_kwargs["language"] = language_hint.strip()

        start_time = time.perf_counter()
        try:
            result = mlx_whisper.transcribe(temp_path, **transcribe_kwargs)
        except Exception as e:
            logger.error(f"mlx-whisper transcription error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

        duration = time.perf_counter() - start_time
        text = result.get("text", "").strip()
        detected_lang = result.get("language") or language_hint or "unknown"

        return TranscribeResponse(
            text=text,
            detected_language=detected_lang,
            duration_seconds=round(duration, 4),
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError as cleanup_err:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {cleanup_err}")
