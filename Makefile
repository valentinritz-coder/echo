.PHONY: setup up down logs

setup:
	cp -n .env.example .env || true

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f
