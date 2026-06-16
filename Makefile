# HackLet League — convenience targets. Run from the repo root.

.PHONY: up down restart logs pull ps config dev migrations test

up:        ## Start the stack (detached)
	docker compose up -d

down:      ## Stop the stack
	docker compose down

restart:   ## Recreate the stack
	docker compose up -d --force-recreate

logs:      ## Tail logs (Ctrl-C to stop)
	docker compose logs -f

pull:      ## Pull latest images
	docker compose pull

ps:        ## Show running services
	docker compose ps

config:    ## Validate compose + show resolved config
	docker compose config

dev:       ## Run with the dev override (bind-mounted source, autoreload)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up

migrations: ## Generate Django migrations (persisted to host via the dev override)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm backend uv run python manage.py makemigrations

test:      ## Run the pytest suite (dev deps installed into the dev-override venv)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml run --rm backend uv run --group dev pytest
