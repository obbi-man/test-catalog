.PHONY: up down logs test test-backend build-frontend config polling

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f backend nginx

config:
	docker compose config -q

test: test-backend

test-backend:
	cd backend && python -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt && .venv/bin/pytest -q

build-frontend:
	cd frontend && npm install && npm run build

# Локальная разработка без вебхука (нужен BOT_MODE=polling и доступные postgres/minio)
polling:
	cd backend && python -m app.bot.polling
