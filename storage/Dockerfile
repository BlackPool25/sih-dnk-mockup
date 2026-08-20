# sih-dnk-storage-base — shared base image for auth/ and backend-core/.
# Bakes in the storage Python dependencies so downstream Dockerfiles need
# only `FROM sih-dnk-storage-base` and add their own deps on top.
FROM python:3.12-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# uv for dependency management (copies instead of symlinks — slim-friendly)
RUN pip install --no-cache-dir uv
ENV UV_LINK_MODE=copy

# Place the storage package at /opt/storage so the parent (/opt) is on
# PYTHONPATH, making `from storage.db import ...` resolve correctly.
WORKDIR /opt/storage

# Copy everything for uv sync (hatchling needs source files to build the
# local package; only-include skips name-based auto-detection).
COPY pyproject.toml __init__.py config.py crypto.py db.py redis.py ./
COPY tests/ tests/
RUN uv sync --no-dev

# PYTHONPATH includes /opt — the parent of the storage package.
ENV PYTHONPATH=/opt
# Activate the venv so system python uses installed packages.
ENV PATH="/opt/storage/.venv/bin:$PATH"
# Default WORKDIR for downstream images that build FROM this base.
WORKDIR /app

CMD ["sleep", "infinity"]

# ---------------------------------------------------------------------------
# Test stage — full dependency set (incl. dev groups) for running pytest in CI.
# Build with: docker build --target test -t sih-dnk-storage:test .
# ---------------------------------------------------------------------------
FROM runtime AS test
WORKDIR /opt/storage
COPY uv.lock ./
RUN uv sync --frozen
CMD ["uv", "run", "pytest"]
