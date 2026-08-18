# SIH-DNK validation-engine — built on the shared python base
# (docker/Dockerfile.python: python:3.12-slim + weasyprint system deps + uv).
#
# Code is bind-mounted at runtime by docker-compose.yml (.:/app), so this
# image only carries the uv-synced dependency environment. CMD inherited from
# the base image is `sleep infinity` (overridden once the FastAPI server lands).

FROM sih-dnk-python-base AS runtime

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# ---------------------------------------------------------------------------
# Test stage — full dependency set (incl. dev groups) for running pytest in CI.
# Build with: docker build --target test -t sih-dnk-validation-engine:test .
# ---------------------------------------------------------------------------
FROM runtime AS test
RUN uv sync --frozen
CMD ["uv", "run", "pytest"]
