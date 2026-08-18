# sih-dnk-backend-core — FastAPI service built on top of the auth image.
# Inherits Python 3.12, uv, storage + auth deps from sih-dnk-auth.
FROM sih-dnk-auth AS runtime

WORKDIR /opt/backend-core

# Install backend-core deps; uv creates its own .venv at /opt/backend-core/.venv
# and resolves the sih-dnk-storage + sih-dnk-auth path deps from /opt/storage and /opt/auth.
COPY pyproject.toml ./
RUN uv sync --no-dev

RUN mkdir -p /opt/backend-core
COPY app/ app/
COPY tests/ tests/

# PYTHONPATH must include both /opt (for auth.* and storage.* imports) and
# /opt/backend-core (for app.* imports).
ENV PYTHONPATH="/opt/backend-core:/opt"

# PATH includes all three venvs so fastapi, uvicorn, httpx (backend-core),
# PyJWT, passlib (auth), and sqlalchemy, redis (storage) are all reachable.
ENV PATH="/opt/backend-core/.venv/bin:/opt/auth/.venv/bin:/opt/storage/.venv/bin:$PATH"
WORKDIR /app
CMD ["sleep", "infinity"]

# ---------------------------------------------------------------------------
# Test stage — full dependency set (incl. dev groups) for running pytest in CI.
# Build with: docker build --target test -t sih-dnk-backend-core:test .
# ---------------------------------------------------------------------------
FROM runtime AS test
WORKDIR /opt/backend-core
COPY uv.lock ./
RUN uv sync --frozen
CMD ["uv", "run", "pytest"]
