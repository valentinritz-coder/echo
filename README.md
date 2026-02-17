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
curl http://localhost:8000/health
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
   - récupère `GET /questions/today`
   - upload audio (multipart) via `POST /entries`
3. Onglet **Bibliothèque**:
   - liste `GET /entries?user_id=...`
   - lecture audio via `GET /entries/{id}/audio` (en Docker, Streamlit récupère les bytes côté serveur/proxy au clic **▶ Lire**)
   - bouton **Télécharger** avec un nom de fichier incluant une extension cohérente avec `audio_mime`
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
