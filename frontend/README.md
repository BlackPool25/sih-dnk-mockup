# frontend — SIH-DNK Mockup

Minimal **placeholder** frontend served by `nginx:alpine`. Toolchain/framework is
**TBD** (Nabiha chooses — see `../.omo/plans/project-scaffolding.md`).

## Ports

| Host port | Container port | Notes          |
|-----------|----------------|----------------|
| `8005`    | `80`           | nginx:alpine   |

## Run

```sh
# Build & run standalone (from repo root):
docker build -t sih-dnk-frontend -f frontend/Dockerfile frontend/
docker run --rm -p 127.0.0.1:8005:80 sih-dnk-frontend

# Or bring the whole stack up (redis + all 5 services):
docker compose up -d
```

Then open <http://localhost:8005>.

## Files

- `Dockerfile` — `FROM nginx:alpine`, copies `index.html` into the default web root.
- `index.html` — minimal placeholder page.
