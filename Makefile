# HackLet League — convenience targets. Run from the repo root.

.PHONY: up down restart logs pull ps config

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
