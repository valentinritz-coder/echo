# Tests Streamlit en local (apps/web)

Guide minimal et **vérifié** pour tester l'UI Streamlit (`apps/web`) avec l'API FastAPI (`services/api`).

## 1) Audit rapide: ce qui existe dans ce repo

### Statut des éléments demandés

- **EXISTE** — `Makefile`
- **EXISTE** — workflow GitHub Actions: `.github/workflows/ci.yml` (nom: `CI`)
- **EXISTE** — dossier E2E: `services/api/tests_e2e/`
- **EXISTE** — client web: `apps/web/api_client.py`
- **EXISTE** — variables d'env d'exemple: `.env.example`
- **EXISTE** — endpoint freeze: `POST /api/v1/entries/{entry_id}/freeze`
- **EXISTE** — endpoint login: `POST /api/v1/auth/login`

### Où chercher dans le repo

- Vue d'ensemble + démarrage Docker + migrations + tests API/E2E: `README.md`
- Commandes utilitaires Docker (`up/down/logs`): `Makefile`
- Pipeline CI (lint + tests): `.github/workflows/ci.yml`
- Endpoints API: `services/api/app/main.py`, `services/api/app/routes/auth.py`, `services/api/app/routes/system.py`
- E2E API: `services/api/tests_e2e/`
- Client HTTP Streamlit: `apps/web/api_client.py`
- Variables d'environnement d'exemple: `.env.example`

---

## 2) Prérequis

- Python 3.11+
- Docker + Docker Compose (recommandé pour un run local rapide)
- Copier `.env.example` vers `.env`

### `.env` (strictement basé sur `.env.example`)

Variables présentes dans `.env.example`:

- `APP_ENV`
- `DATA_DIR`
- `API_BASE_URL`

Création du `.env`:

**Linux/macOS**

```bash
cp .env.example .env
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

> Note importante: le web lit `ECHO_API_URL` dans `apps/web/api_client.py` (fallback `http://localhost:8000`).
> Dans `docker-compose.yml`, le service `web` injecte `API_BASE_URL`, qui n'est pas lu par `apps/web/api_client.py`.
> En local, définissez donc `ECHO_API_URL` si besoin.

---

## 3) Lancer API + Streamlit

## Option A — Docker Compose (depuis la racine)

Services déclarés dans `docker-compose.yml`: `api` et `web`.

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

Vérifications:

```bash
curl http://localhost:8000/api/v1/health
```

Ouvrir ensuite: `http://localhost:8501`

Si vous avez un doute sur les services actifs:

```bash
docker compose ps
```

## Option B — Sans Docker (2 terminaux)

### Terminal 1: API (`services/api`)

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

### Terminal 2: Web (`apps/web`)

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

---

## 4) Smoke tests manuels (orientés utilisateur)

## Jeu A — Login

1. Ouvrir `http://localhost:8501`
2. Saisir email + mot de passe dans la sidebar
3. Cliquer **Se connecter**
4. Attendu: message de succès + accès aux onglets de création/liste

## Jeu B — Création d'une entry

1. Onglet **New memory / Créer un souvenir**
2. Ajouter du texte (optionnel)
3. Ajouter un audio (optionnel)
4. Cliquer **Save**
5. Attendu: entry visible ensuite dans **List / Mes souvenirs**

## Jeu C — Liste / pagination

1. Créer plusieurs entrées
2. Onglet **List / Mes souvenirs**
3. Vérifier **Prev** / **Next**
4. Attendu: variation de `offset`, navigation cohérente

## Jeu D — Freeze (endpoint API existant)

L'UI ne montre pas de bouton freeze dédié.

1. Créer une entry
2. Appeler `POST /api/v1/entries/{entry_id}/freeze`
3. Tenter une modification (`PATCH /api/v1/entries/{entry_id}` ou remplacement audio)
4. Attendu: refus de modification (erreur métier côté API)

## Jeu E — Erreurs attendues

- token invalide/expiré -> 401
- entry inexistante -> 404
- accès à une entry d'un autre utilisateur -> 403
- upload invalide/trop gros -> 4xx (souvent 422/413 selon validation/limite)

---

## 5) Vérifier l'API quand l'UI bug

## Endpoints utiles (vérifiés dans le code)

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `GET /api/v1/health`
- `GET /api/v1/readyz`
- `GET /api/v1/questions/today`
- `POST /api/v1/entries`
- `GET /api/v1/entries`
- `GET /api/v1/entries/{entry_id}`
- `POST /api/v1/entries/{entry_id}/freeze`
- `POST /api/v1/entries/{entry_id}/assets`
- `GET /api/v1/entries/{entry_id}/assets`
- `GET /api/v1/assets/{asset_id}`
- `GET /api/v1/entries/{entry_id}/audio`
- `PATCH /api/v1/entries/{entry_id}`
- `POST /api/v1/entries/{entry_id}/audio`
- `DELETE /api/v1/entries/{entry_id}/audio`
- `DELETE /api/v1/entries/{entry_id}`

## Login + token

**Linux/macOS (curl)**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@example.com","password":"admin-password"}'
```

**Windows PowerShell**

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/v1/auth/login" -ContentType "application/json" -Body '{"email":"admin@example.com","password":"admin-password"}'
```

## Checks minimaux

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

---

## 6) Debug rapide

## Logs API

### Docker

**Linux/macOS / PowerShell**

```bash
docker compose logs -f api
```

### Sans Docker

- regarder la sortie du process `uvicorn` (terminal API)

## Logs Streamlit

### Docker

**Linux/macOS / PowerShell**

```bash
docker compose logs -f web
```

### Sans Docker

- regarder la sortie du process `streamlit run app.py` (terminal web)

---

## 7) Checklist régression rapide

- [ ] login OK / KO
- [ ] chargement question du jour après login
- [ ] création entrée texte
- [ ] création entrée avec audio
- [ ] liste des entrées visible
- [ ] pagination Prev/Next fonctionnelle
- [ ] lecture audio disponible si fichier présent
- [ ] erreurs auth/ACL cohérentes (401/403/404)
- [ ] freeze empêche bien les modifications

---

## 8) Tests automatisables réalistes (bonus)

Déjà présents côté API:

- `services/api/tests/test_auth.py`
- `services/api/tests/test_entries_list.py`
- `services/api/tests/test_freeze.py`
- `services/api/tests/test_upload.py`
- E2E HTTP Docker: `services/api/tests_e2e/`

Commandes utiles:

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
