"""pricing-engine placeholder entrypoint.

Scaffold only — no business logic. Provides a stub FastAPI app so the dev
run path (`uv run uvicorn main:app`) works out of the box; the Docker
entrypoint is `sleep infinity` until the pricing team implements a real one.
"""

from fastapi import FastAPI

app = FastAPI(title="pricing-engine", version="0.1.0")


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
