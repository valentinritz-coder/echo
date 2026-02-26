.PHONY: setup up down logs backup restore

setup:
	cp -n .env.example .env || true

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

backup:
	./scripts/backup.sh

restore:
	@if [ -z "$(BACKUP)" ]; then \
		echo "Usage: make restore BACKUP=backups/echo_backup_YYYYmmdd_HHMMSSZ.tar.gz"; \
		exit 1; \
	fi
	./scripts/restore.sh "$(BACKUP)"
