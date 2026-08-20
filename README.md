# SIH-DNK Mockup

One-command turnup (frontend docker 127.0.0.1:8005 healthy):

```sh
make up        # auto-creates .env from .env.example if missing, then docker compose up --build -d
make health    # bash scripts/check_health.sh — all services 200
make logs      # docker compose logs -f
make down      # docker compose down
```

Manual equivalent:
```sh
bash scripts/setup_env.sh   # idempotent: keeps valid .env symlink, replaces broken symlink, copies .env.example if missing
docker compose up --build -d
curl -f http://127.0.0.1:8005/   # frontend via nginx -> backend-core
```

Ports (all 127.0.0.1 only):
5433 db | 6379 redis | 8001 validation | 8002 voice | 8003 pricing | 8004 tracking | 8005 frontend | 8006 backend-core | 8007 marketplace | 8008 verification | 8009 messaging

Frontend: nginx:alpine serving dist/ on :80 inside container, exposed as 127.0.0.1:8005:80, healthcheck `curl -f http://localhost:80/`, depends_on backend-core healthy, proxies /api,/auth,/orders,/docs,/payments,/tracking,/pricing,/messages,/quotes,/verify,/guidance to http://backend-core:8000.
