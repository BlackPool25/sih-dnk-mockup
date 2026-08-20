.PHONY: up down logs health setup-env

setup-env:
	@bash scripts/setup_env.sh

up: setup-env
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

health:
	bash scripts/check_health.sh
