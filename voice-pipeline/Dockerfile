# voice-pipeline image.
# Builds on the shared sih-dnk base (python 3.12-slim + weasyprint deps + uv).
# Base image WORKDIR is /app.
FROM sih-dnk-python-base

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Real entrypoint.  Docker runs CPU-int8 STT (no ROCm passthrough); the
# GPU/ROCm path is the local-dev route via scripts/setup_rocm.sh.
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
