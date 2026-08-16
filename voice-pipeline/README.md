# Voice Pipeline Service (`voice-pipeline`)

A local speech-to-text (STT) microservice built with **FastAPI** and **MLX-Whisper**, specifically optimized for Apple Silicon (M-series chips). It delivers sub-second local transcription for multi-lingual audio inputs from Indian artisans.

---

## ⚡ Key Features

- **Local Inference Engine**: Powered by `mlx-whisper` using the `whisper-large-v3-turbo` model.
- **Lifespan Model Caching**: Loads and caches weights into unified memory once at server startup (eliminating per-request cold-start latency).
- **Multi-Format Ingestion**: Supports `.m4a`, `.wav`, `.mp3`, `.ogg`, and `.webm` audio recordings via multipart/form-data upload.
- **Language Guidance**: Accepts optional `language_hint` parameters (`en`, `hi`, `kn`, `mr`, `ta`, etc.) or performs automatic multi-lingual language detection.
- **Zero Cloud Dependency**: Transcribes sensitive artisan speech completely offline without cloud API costs or external network dependencies.

---

## 🔌 API Specification

### 1. Health Check
```http
GET /healthz
```
**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "mlx-community/whisper-large-v3-turbo"
}
```

### 2. Audio Transcription
```http
POST /transcribe
Content-Type: multipart/form-data
```

**Parameters:**
- `file` *(UploadFile, Required)*: The audio file binary stream.
- `language_hint` *(Form[str], Optional)*: ISO 639-1 language code (e.g., `en`, `hi`, `kn`).

**Sample Request (cURL):**
```bash
curl -X POST "http://127.0.0.1:8002/transcribe" \
  -F "file=@recording.m4a" \
  -F "language_hint=hi"
```

**Sample Response (JSON):**
```json
{
  "text": "12 जूट बैग जर्मनी भेजने हैं 500 ग्राम वजन 15000 रुपए की कीमत",
  "language": "hi",
  "model": "mlx-community/whisper-large-v3-turbo",
  "duration_seconds": 1.12
}
```

---

## 🛠️ Local Setup & Execution

### 1. Install Dependencies
Using `uv`:
```bash
cd voice-pipeline
uv sync
```

### 2. Run the Service
```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8002
```

### 3. Verify STT Integration
Run the standalone STT verification script against sample audio files:
```bash
uv run python scripts/verify_stt.py
```
