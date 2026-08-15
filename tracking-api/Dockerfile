# tracking-api placeholder image.
# Builds on the shared sih-dnk base (python 3.12-slim + weasyprint deps + uv).
# Base image WORKDIR is /app; CMD is overridden here to keep the placeholder
# container alive until the tracking team ships a real entrypoint.
FROM sih-dnk-python-base
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
