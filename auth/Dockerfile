# sih-dnk-auth — auth service image built on top of the shared storage base.
# Inherits Python 3.12, uv, and all storage dependencies from sih-dnk-storage-base.
FROM sih-dnk-storage-base

WORKDIR /opt/auth

# Install auth deps; uv creates its own .venv at /opt/auth/.venv and
# resolves the sih-dnk-storage path dep from /opt/storage.
COPY pyproject.toml ./
RUN uv sync --no-dev

RUN mkdir -p /opt/auth
COPY __init__.py deps.py ./
COPY models/ models/
COPY services/ services/
COPY routes/ routes/
COPY middleware/ middleware/
COPY cli/ cli/
COPY tests/ tests/

# PYTHONPATH already set by the base image to /opt.
# Prepend auth venv to PATH so PyJWT, passlib, alembic etc. are reachable
# (storage venv comes second for base deps like sqlalchemy, redis).
ENV PATH="/opt/auth/.venv/bin:/opt/storage/.venv/bin:$PATH"
WORKDIR /app
CMD ["sleep", "infinity"]
