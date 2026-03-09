# Tests et vérifications

Ce document regroupe : le parcours utilisateur (test V1), le lancement en local pour le développement, et les tests automatisés.

---

## 1. Tester en tant qu’utilisateur (parcours V1)

Permet à un testeur (sans connaissance du code) de lancer l’application et de vérifier : connexion → création d’un souvenir → consultation de la liste.

### Prérequis

- **Docker** et **Docker Compose** installés et fonctionnels.
- Un clone du dépôt à jour.

### Préparer l’environnement

1. **Fichier `.env`** — À la racine, copier `.env.example` vers `.env` :
   ```bash
   copy .env.example .env
   ```
   (Sous Linux/macOS : `cp .env.example .env`.)

2. **Compte test et JWT** — `.env.example` contient `ADMIN_EMAIL`, `ADMIN_PASSWORD` et les secrets JWT. Sans eux, la connexion affiche « JWT secrets are not configured ».

3. **Lancer les services** — À la racine :
   ```bash
   docker compose up --build
   ```
   (Ou `docker compose up -d --build` en arrière-plan.)

4. **Appliquer les migrations** — Dans un autre terminal :
   ```bash
   docker compose exec api alembic upgrade head
   ```
   À faire une fois au premier run (et après chaque nouvelle migration).

### Accéder à l’application

- **Interface web** : [http://localhost:8501](http://localhost:8501)

### Parcours

1. **Se connecter** — Dans la barre latérale gauche : email et mot de passe du compte test (`ADMIN_EMAIL` / `ADMIN_PASSWORD`), puis « Se connecter ».
2. **Créer un souvenir** — Onglet « New memory / Créer un souvenir » : question du jour, puis au moins un parmi texte / audio / images, puis « Save ».
3. **Consulter la bibliothèque** — Onglet « List / Mes souvenirs » : liste paginée (Prev/Next), lecture audio et affichage des images.

### En cas de problème

- **« Connexion refusée » ou « JWT secrets are not configured »** : vérifier `JWT_SECRET_KEY` et `JWT_REFRESH_SECRET_KEY` dans `.env`, et que les conteneurs tournent (`docker compose ps`).
- **Page blanche ou erreur web** : appliquer les migrations et vérifier l’API : `curl http://localhost:8000/api/v1/health` doit retourner `{"status":"ok"}`.

**Exposer l’app pour un test externe** (tunnel, déploiement minimal) : voir [Exposer l’app pour un test externe](deploy-test.md).

---

## 2. Développement local (API + Streamlit)

Pour développer sans Docker : lancer l’API et Streamlit séparément.

### Prérequis

- Python 3.11+
- Fichier `.env` à la racine (copier depuis `.env.example`).

En local hors Docker, définir `ECHO_API_URL=http://localhost:8000` pour que Streamlit joigne l’API.

### Option A — Docker Compose (recommandé)

À la racine :

```bash
docker compose up --build
docker compose exec api alembic upgrade head
```

- API : http://localhost:8000  
- Streamlit : http://localhost:8501

### Option B — Sans Docker (2 terminaux)

**Terminal 1 — API** (`services/api`) :

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate   # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
DATA_DIR=../../data alembic upgrade head
DATA_DIR=../../data uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Streamlit** (`apps/web`) :

```bash
cd apps/web
python -m venv .venv
source .venv/bin/activate
pip install -e .
ECHO_API_URL=http://localhost:8000 streamlit run app.py --server.address=0.0.0.0 --server.port=8501
```

### Vérifications rapides

- Santé API : `curl http://localhost:8000/api/v1/health` et `curl http://localhost:8000/api/v1/readyz`
- Routes : `services/api/app/main.py`, `services/api/app/routes/`
- Logs : `docker compose logs -f api` / `docker compose logs -f web` (ou sortie des terminaux en local)

---

## 3. Tests automatisés

### Tests API (pytest)

Depuis la racine :

```bash
pip install -e "services/api[dev]"
pytest services/api/tests -q
```

### Tests E2E (stack Docker)

Prérequis : Docker actif. Optionnel sans rebuild : `E2E_NO_BUILD=1`.

```bash
python -m pytest -q services/api/tests_e2e
```

PowerShell :

```powershell
$env:PYTHONUTF8="1"; $env:RUN_E2E="1"
python -m pytest services/api/tests_e2e -q -vv
```

### Checklist régression manuelle (UI)

- [ ] Login
- [ ] Question du jour
- [ ] Création souvenir (texte, audio)
- [ ] Liste et pagination Prev/Next
- [ ] Lecture audio
- [ ] Erreurs 4xx affichées correctement
