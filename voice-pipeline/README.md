# voice-pipeline

Speech-to-text (STT) + text-to-speech (TTS) microservice for the SIH DNK mockup —
the voice layer of the Hindi-first export assistant. All voice operations run on
the **Sarvam AI** cloud API.

| Operation | Sarvam model |
| --------- | ------------ |
| STT | `saaras:v3` (`/speech-to-text`) |
| TTS | `bulbul:v2`, speaker `anushka` (`/text-to-speech`) |
| Translate | `mayura:v1` (`/translate`) |

## Ports

| Binding | Port |
| ------- | ---- |
| Host (docker-compose mapping) | **8002** |
| Container (uvicorn) | **8000** |

## API

- `GET /healthz` → `{status, provider}` (`provider` is always `sarvam`)
- `POST /transcribe` — multipart `file` + optional `language_hint` → `{transcript, language, duration_ms, provider, word_count, low_confidence, language_probability?}` (`language_probability` is present only when Sarvam returns it)
- `POST /tts` — JSON `{text, language}` → `audio/wav` bytes (text longer than 400 chars → 400)
- `POST /translate` — JSON `{input, source_language_code, target_language_code}` → `{translated_text}`

## Run

```bash
uv sync
uv run uvicorn main:app --port 8002
```

## Environment

| Var | Default | Purpose |
| --- | ------- | ------- |
| `SARVAM_API_KEY` | — | Sarvam subscription key (header `api-subscription-key`) |

Sarvam is the only STT/TTS provider — no local engines are bundled.

The backend-core router proxies this service under `/api/voice/*` (auth-protected).
