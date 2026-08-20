# marketplace — FastAPI service on sih-dnk-python-base
FROM sih-dnk-python-base
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen 2>/dev/null || uv sync --no-dev
COPY . .
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
