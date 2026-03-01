# Tests Streamlit en local (apps/web)

Guide local pour tester l'UI Streamlit (`apps/web`) avec l'API FastAPI (`services/api`) en restant aligné avec les fichiers réellement présents dans ce repo.

## 1) Où trouver l'info dans le repo

- Démarrage projet, migrations, endpoints documentés et tests: `README.md`
- Commandes utilitaires Docker: `Makefile`
- Workflow CI présent: `.github/workflows/ci.yml`
- Compose utilisé dans ce repo: `docker-compose.yml` (services `api` et `web`)
- Variables d'environnement d'exemple: `.env.example`
- Client HTTP utilisé par Streamlit: `apps/web/api_client.py`
- Routes API implémentées: `services/api/app/main.py`, `services/api/app/routes/auth.py`, `services/api/app/routes/system.py`
- Dossier E2E API: `services/api/tests_e2e/`

## 2) Prérequis

- Python 3.11+
- Docker + Docker Compose (recommandé)
- Fichier `.env` à la racine

Créer `.env`:

**Linux/macOS**

```bash
cp .env.example .env
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Variables présentes dans `.env.example` (et uniquement celles-ci):

- `APP_ENV`
- `DATA_DIR`
- `API_BASE_URL`

### Point important sur l'URL API côté Streamlit

- `apps/web/api_client.py` lit la variable `ECHO_API_URL` (fallback: `http://localhost:8000`).
- `docker-compose.yml` injecte `API_BASE_URL` au service `web`.

Conséquence pratique: en exécution locale hors Docker, définissez `ECHO_API_URL` explicitement.

## 3) Lancer API + Streamlit

### Option A — Docker Compose (racine du repo)

**Linux/macOS**

```bash
docker compose up --build
docker compose exec api alembic upgrade head
```

**Windows PowerShell**

```powershell
docker compose up --build
docker compose exec api alembic upgrade head
```

Vérifier les services actifs:

```bash
docker compose ps
```

Vérifier API:

```bash
curl http://localhost:8000/api/v1/health
```

UI Streamlit: `http://localhost:8501`

### Option B — Sans Docker (2 terminaux)

#### Terminal 1: API (`services/api`)

**Linux/macOS**

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
DATA_DIR=../../data alembic upgrade head
DATA_DIR=../../data uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Windows PowerShell**

```powershell
cd services/api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
$env:DATA_DIR="../../data"; alembic upgrade head
$env:DATA_DIR="../../data"; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Streamlit (`apps/web`)

**Linux/macOS**

```bash
cd apps/web
python -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e .
ECHO_API_URL=http://localhost:8000 streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

**Windows PowerShell**

```powershell
cd apps/web
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e .
$env:ECHO_API_URL="http://localhost:8000"; streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

## 4) Smoke tests manuels (UI)

## A. Login

1. Ouvrir `http://localhost:8501`
2. Renseigner email + mot de passe dans la sidebar
3. Cliquer **Se connecter**
4. Attendu: accès aux onglets de création/liste

> Le repo expose `POST /api/v1/auth/login`, mais ce guide ne suppose pas d'identifiants par défaut.

## B. Création d'un souvenir

1. Onglet **New memory / Créer un souvenir**
2. Saisir un texte (optionnel)
3. Ajouter un audio (optionnel)
4. Cliquer **Save**
5. Attendu: souvenir visible dans **List / Mes souvenirs**

## C. Liste et pagination

1. Créer plusieurs souvenirs
2. Aller sur **List / Mes souvenirs**
3. Utiliser **Prev** / **Next**
4. Attendu: navigation cohérente entre pages

## D. Erreurs attendues

- Si token invalide/non présent: 4xx attendu
- Si ressource absente: 4xx attendu
- Si upload invalide: 4xx attendu

## 5) Vérifier l'API quand l'UI bug

Commandes minimales:

**Linux/macOS**

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/readyz
```

**Windows PowerShell**

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/health"
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/api/v1/readyz"
```

Pour la liste complète des routes réellement implémentées, vérifier:

- `services/api/app/main.py`
- `services/api/app/routes/auth.py`
- `services/api/app/routes/system.py`

## 6) Debug rapide

### Logs API

**Docker**

```bash
docker compose logs -f api
```

**Sans Docker**

- suivre la sortie du terminal `uvicorn`

### Logs Streamlit

**Docker**

```bash
docker compose logs -f web
```

**Sans Docker**

- suivre la sortie du terminal `streamlit run app.py`

## 7) Checklist régression rapide

- [ ] Login UI
- [ ] Chargement question du jour
- [ ] Création souvenir texte
- [ ] Création souvenir avec audio
- [ ] Affichage liste
- [ ] Pagination Prev/Next
- [ ] Lecture audio si présent
- [ ] Erreurs 4xx correctement affichées en cas d'échec

## 8) Tests auto déjà présents (API)

- `services/api/tests/test_auth.py`
- `services/api/tests/test_entries_list.py`
- `services/api/tests/test_freeze.py`
- `services/api/tests/test_upload.py`
- `services/api/tests_e2e/`

Commandes:

**Linux/macOS**

```bash
python -m pip install -e "services/api[dev]"
python -m pytest -q services/api/tests
python -m pytest -q services/api/tests_e2e
```

**Windows PowerShell**

```powershell
python -m pip install -e "services/api[dev]"
python -m pytest -q services/api/tests
python -m pytest -q services/api/tests_e2e
```
