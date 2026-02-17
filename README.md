# echo-mvp

MVP "capsule de vie" — Phase 2 (SQLite + upload audio + bibliothèque, sans IA).

## Prérequis

- Docker + Docker Compose
- (Optionnel) Python 3.11+ pour exécution locale sans Docker

## Démarrage rapide (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Puis ouvrir:
- API: http://localhost:8000/health
- Web: http://localhost:8501

## Base SQLite + migrations

La base SQLite est stockée dans `data/echo.db` (monté dans `/app/data` côté conteneur).

Commandes de migration (depuis `services/api`) :

```bash
alembic upgrade head
alembic downgrade -1
```

> L'application crée aussi les tables au démarrage pour éviter un écran vide en local, mais le flux recommandé reste Alembic.

## Flux fonctionnel MVP

1. Dans Streamlit, saisir un `user_id` (auth simplifiée de phase 2).
2. Onglet **Question du jour**:
   - récupère `GET /questions/today`
   - upload audio (multipart) via `POST /entries`
3. Onglet **Bibliothèque**:
   - liste `GET /entries?user_id=...`
   - lecture audio via `GET /entries/{id}/audio`
   - suppression via `DELETE /entries/{id}`

## Contraintes upload

- Taille max: **25 MB**
- MIME autorisés:
  - `audio/mpeg`
  - `audio/mp4`
  - `audio/x-m4a`
  - `audio/wav`
  - `audio/ogg`
- Stockage fichier: `data/audio/{entry_id}.{ext}` avec `entry_id` UUID
- `DELETE /entries/{id}` supprime la ligne DB + le fichier audio

## Endpoints API

- `GET /health`
- `GET /version`
- `GET /questions/today`
- `POST /entries` (multipart: `user_id`, `question_id`, `audio_file`)
- `GET /entries?user_id=...`
- `GET /entries/{id}`
- `GET /entries/{id}/audio`
- `DELETE /entries/{id}`

Erreurs JSON harmonisées pour validation et erreurs métier (`422`, `404`, `500`).

## Tests

Depuis `services/api`:

```bash
pip install -e ".[dev]"
pytest
```

Les tests couvrent le minimum demandé:
- create/list/delete
- 404
- validation MIME

## Variables d'environnement

Exemple dans `.env.example`:

- `APP_ENV`: environnement applicatif (`development` par défaut)
- `OPENAI_API_KEY`: optionnelle pour des tâches futures IA
- `DATA_DIR`: dossier de données local (`./data`)
- `API_BASE_URL`: URL de l'API consommée par Streamlit (`http://api:8000` dans Docker)

## Structure du projet

```text
.
├── apps/
│   └── web/
│       ├── app.py
│       ├── Dockerfile
│       └── pyproject.toml
├── data/
│   └── audio/
│       └── .gitkeep
├── docs/
│   ├── privacy.md
│   └── product.md
├── services/
│   └── api/
│       ├── alembic/
│       │   ├── env.py
│       │   └── versions/
│       ├── app/
│       │   ├── db.py
│       │   ├── main.py
│       │   ├── models.py
│       │   ├── schemas.py
│       │   └── settings.py
│       ├── tests/
│       ├── alembic.ini
│       ├── Dockerfile
│       └── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
└── Makefile
```
