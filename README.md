# echo-mvp

## Quickstart Windows (Docker)

### A) Ouvrir PowerShell dans le dossier du repo

```powershell
cd C:\Users\Valentin\Documents\echo
```

### B) Mettre à jour le repo depuis GitHub

```powershell
git status
git pull
```

Si `git pull` refuse à cause de modifications locales non commit:

```powershell
git stash push -m "wip"
git pull
git stash pop
```

### C) Préparer le fichier `.env` (si absent)

Si `.env` n'existe pas:

```powershell
copy .env.example .env
```

Alternative PowerShell:

```powershell
Copy-Item .env.example .env
```

### D) Créer les dossiers de données (DB + audios)

```powershell
mkdir data -ErrorAction SilentlyContinue
mkdir data\audio -ErrorAction SilentlyContinue
```

### E) Démarrer Docker Desktop

Docker Desktop doit être lancé et en état **Running**.

Vérifier les commandes Docker:

```powershell
docker --version
docker compose version
```

### F) Lancer l'app avec Docker Compose

Première fois (ou après changements):

```powershell
docker compose up --build
```

Variante en arrière-plan:

```powershell
docker compose up -d --build
```

### G) Appliquer les migrations Alembic

Indispensable au premier run, et après ajout de nouvelles migrations.

Si la DB est vide, l'API logge un warning du type: `Database not initialized. Run: alembic upgrade head`.

Lancer la migration:

```powershell
docker compose exec api alembic upgrade head
```

Vérification optionnelle:

```powershell
docker compose exec api alembic current
```

### H) Vérifier que tout tourne

API:

```powershell
curl http://localhost:8000/api/v1/health
```

Web:

- ouvrir http://localhost:8501

Données persistées sur l'hôte:

- DB: `.\data\echo.db`
- audios: `.\data\audio\`

### I) Commandes utiles

Voir les conteneurs:

```powershell
docker compose ps
```

Logs:

```powershell
docker compose logs -f api
docker compose logs -f web
```

Stop:

```powershell
docker compose down
```

Restart sans rebuild:

```powershell
docker compose restart api web
```

MVP "capsule de vie" — Phase 2.5 (SQLite + upload audio + bibliothèque).

## Prérequis

- Docker + Docker Compose
- (Optionnel) Python 3.11+ pour exécution locale sans Docker

## Démarrage rapide (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Puis ouvrir:
- API: http://localhost:8000/api/v1/health
- Web: http://localhost:8501

**Tester (parcours utilisateur, dev local, tests auto)** : voir [Tests et vérifications](docs/testing.md).

**Exposer pour un test externe** (tunnel ou déploiement minimal) : voir [Exposer l’app pour un test externe](docs/deploy-test.md).

## Base SQLite + migrations

La base SQLite est stockée dans `data/echo.db` (monté dans `/app/data` côté conteneur).

Le schéma n'est **pas** créé automatiquement au démarrage de l'API. Si la DB n'est pas initialisée, l'API logge un warning et vous devez appliquer les migrations Alembic.

En Docker:

```bash
docker compose exec api alembic upgrade head
```

En local (sans Docker, depuis `services/api`):

```bash
DATA_DIR=./data alembic upgrade head
```

Autres commandes utiles Alembic (depuis `services/api`) :

```bash
alembic upgrade head
alembic downgrade -1
```

## Flux fonctionnel MVP

1. Dans Streamlit, saisir un `user_id` (auth simplifiée de phase 2).
2. Onglet **Question du jour**:
   - récupère `GET /api/v1/questions/today`
   - upload audio (multipart) via `POST /api/v1/entries`
3. Onglet **Bibliothèque**:
   - liste `GET /api/v1/entries?user_id=...`
   - lecture audio via `GET /api/v1/entries/{id}/audio` (en Docker, Streamlit récupère les bytes côté serveur/proxy au clic **▶ Lire**)
   - bouton **Télécharger** avec un nom de fichier incluant une extension cohérente avec `audio_mime`
   - suppression via `DELETE /api/v1/entries/{id}`

## Contraintes upload

- Taille max: **25 MB**
- MIME autorisés:
  - `audio/mpeg`
  - `audio/mp4`
  - `audio/x-m4a`
  - `audio/wav`
  - `audio/ogg`
- Stockage fichier: `data/audio/{entry_id}.{ext}` avec `entry_id` UUID
- `DELETE /api/v1/entries/{id}` supprime la ligne DB + le fichier audio

## Endpoints API

- `GET /api/v1/health`
- `GET /api/v1/version`
- `GET /api/v1/questions/today`
- `POST /api/v1/entries` (multipart: `user_id`, `question_id`, `audio_file`)
- `GET /api/v1/entries?user_id=...`
- `GET /api/v1/entries/{id}`
- `GET /api/v1/entries/{id}/audio`
- `DELETE /api/v1/entries/{id}`

Erreurs JSON harmonisées pour validation et erreurs métier (`422`, `404`, `500`).

## Tests Streamlit / développement local

Voir [docs/testing.md](docs/testing.md) (parcours utilisateur, lancement local, tests automatisés).

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
- `DATA_DIR`: dossier de données local (`./data`)
- `API_BASE_URL`: URL de l'API consommée par Streamlit (Docker: `http://api:8000`). En local, on peut aussi utiliser `ECHO_API_URL` (fallback: `http://localhost:8000`)
- `JWT_SECRET_KEY`, `JWT_REFRESH_SECRET_KEY`: secrets JWT (obligatoires pour le login ; voir `.env.example`)
- `ADMIN_EMAIL`, `ADMIN_PASSWORD`: compte test créé au 1er démarrage en dev (voir [docs/testing.md](docs/testing.md))
- `ALLOWED_ORIGINS`: liste CSV des origines CORS autorisées (défaut dev: `http://localhost:3000,http://localhost:8501,http://localhost:8000`)
- `ALLOWED_HOSTS`: liste CSV des hosts HTTP autorisés (`localhost,127.0.0.1,testserver` par défaut)
- `ENABLE_HSTS`: active l'en-tête `Strict-Transport-Security` (`false` par défaut)
- `HSTS_MAX_AGE`: valeur `max-age` pour HSTS (défaut: `31536000`)

## Backups & restore

Voir la documentation dédiée: [`docs/backup_restore.md`](docs/backup_restore.md).

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

## Tests E2E (blackbox HTTP, Docker sandbox)

Ces tests E2E pilotent automatiquement le stack Docker Compose sandbox (`docker-compose.yml` + `docker-compose.sandbox.yml`), appliquent les migrations, attendent le healthcheck, puis valident un flux réel (auth, upload, ACL, listing/pagination, audio, cleanup).

Installer les dépendances dev:

```bash
python -m pip install -e "services/api[dev]"
```

Lancer les E2E:

```bash
python -m pytest -q services/api/tests_e2e
```

Option rapide (sans rebuild d'images):

```bash
E2E_NO_BUILD=1 python -m pytest -q services/api/tests_e2e
```

PowerShell:

```powershell
$env:PYTHONUTF8="1"
$env:PYTHONIOENCODING="utf-8"
$env:RUN_E2E="1"
python -m pytest services/api/tests_e2e -q -vv
```

CMD:

```cmd
set E2E_NO_BUILD=1
python -m pytest -q services/api/tests_e2e
```

Variables utiles:
- `E2E_BASE_URL` (défaut: `http://localhost:8000`)
- `E2E_NO_BUILD` (`1/true/yes` pour sauter `docker compose build`)
