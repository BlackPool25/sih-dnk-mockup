# pricing-engine

Placeholder scaffold for the **pricing engine** component of the SIH DNK mockup
monorepo. Owned by the pricing team — no business logic lives here yet.

## Ports

| Binding | Port |
| ------- | ---- |
| Host (docker-compose mapping) | **8003** |
| Container (uvicorn) | **8000** |

## Upstream dependencies

Consumed via `docker-compose.yml` (see repo root):

- **PostgreSQL** — `DATABASE_URL` (e.g. `postgresql+psycopg://postgres:postgres@postgres:5432/sih_dnk`)
- **Redis** — `REDIS_URL` (e.g. `redis://redis:6379/0`)

These are declared by compose; this component reads them from the environment at
runtime.

## Base image

`Dockerfile` builds on the shared monorepo image **`sih-dnk-python-base`**
(`docker/Dockerfile.python`, python 3.12-slim + WeasyPrint system deps + uv).
Pattern:

```dockerfile
FROM sih-dnk-python-base
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen
CMD ["sleep", "infinity"]   # placeholder until a real entrypoint exists
```

The base image's WORKDIR is `/app` and its default CMD is `sleep infinity`; the
placeholder image overrides CMD explicitly.

## Run

**Container (primary):**

```sh
docker compose up pricing-engine
```

**Local dev:**

```sh
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check: `GET /healthz` → `{"status": "ok"}`.
