# SIH-DNK validation-engine — built on the shared python base
# (docker/Dockerfile.python: python:3.12-slim + weasyprint system deps + uv).
#
# Code is bind-mounted at runtime by docker-compose.yml (.:/app), so this
# image only carries the uv-synced dependency environment. CMD inherited from
# the base image is `sleep infinity` (overridden once the FastAPI server lands).

FROM sih-dnk-python-base

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

COPY . .
