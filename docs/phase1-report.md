# Compte rendu — echo-mvp (après phase 1)

## 1) Arborescence (jusqu'à 3 niveaux)

```text
.
├── .env.example
├── .gitignore
├── Makefile
├── README.md
├── docker-compose.yml
├── apps/
│   └── web/
│       ├── Dockerfile
│       ├── app.py
│       └── pyproject.toml
├── data/
│   └── audio/
│       └── .gitkeep
├── docs/
│   ├── privacy.md
│   ├── product.md
│   └── phase1-report.md
└── services/
    └── api/
        ├── Dockerfile
        ├── pyproject.toml
        └── app/
```

### Fichiers importants

- `README.md`
- `docker-compose.yml`
- `.env.example`
- `services/api/app/main.py`
- `services/api/app/settings.py`
- `apps/web/app.py`
- `docs/product.md`
- `docs/privacy.md`

## 2) Résumé des fichiers clés

- `README.md` : décrit le MVP, les prérequis, le démarrage Docker, les variables d'environnement, la structure projet, les commandes `make`, et ce qui est inclus/exclu en phase 1.
- `docker-compose.yml` : définit 2 services (`api`, `web`), ports exposés (`8000`, `8501`), variables d'environnement, montage `./data:/app/data`, et dépendance `web -> api`.
- `.env.example` : valeurs par défaut pour `APP_ENV`, `OPENAI_API_KEY`, `DATA_DIR`, et `API_BASE_URL`.
- `services/api/app/main.py` : FastAPI minimal avec endpoints `GET /health` (`{"status":"ok"}`) et `GET /version` (`name`, `version`).
- `services/api/app/settings.py` : configuration via `pydantic-settings` (`app_name`, `app_version`, `app_env`, `data_dir`) avec lecture `.env`.
- `apps/web/app.py` : app Streamlit qui affiche le projet et teste l'API via `requests.get({API_BASE_URL}/health)` avec message succès/avertissement.
- `docs/product.md` : vision produit MVP “capsule de vie”, stockage local, progression par itérations, robustesse du socle.
- `docs/privacy.md` : principes de confidentialité (local-first, consentement, suppression utilisateur, sensibilité des audios).

## 3) Vérification du démarrage (api + web)

### Vérification Docker Compose

- La commande cible est bien `docker compose up --build` (ou `docker compose up`).
- Dans cet environnement de vérification, `docker` n'est pas installé, donc la vérification directe des 2 conteneurs n'a pas pu être exécutée ici.

### Vérification fonctionnelle équivalente (locale)

Exécution locale des 2 apps Python :

- API lancée avec Uvicorn sur `:8000`
- Web Streamlit lancé sur `:8501` avec `API_BASE_URL=http://127.0.0.1:8000`
- Checks validés :
  - `GET /health` retourne `{"status":"ok"}`
  - `GET /version` retourne `{"name":"echo-mvp","version":"0.1.0"}`
  - L'interface Streamlit affiche bien: `API en ligne: {'status': 'ok'}`

Aucune correction de code n'a été nécessaire.

## 4) Commandes exactes

### Lancer le projet

```bash
cp .env.example .env
docker compose up --build
```

### Arrêter

```bash
docker compose down
```

### (Optionnel) Relancer proprement en supprimant les volumes

```bash
docker compose down -v
docker compose up --build
```

## 5) TODO phase 2 (API + SQLite + upload audio)

- [ ] Ajouter SQLite (schéma initial + migrations).
- [ ] Créer un modèle `Recording` (id, titre, chemin fichier, durée, date création).
- [ ] Ajouter endpoint API `POST /recordings` (métadonnées).
- [ ] Ajouter endpoint API `GET /recordings` (liste paginée).
- [ ] Ajouter endpoint API `GET /recordings/{id}`.
- [ ] Ajouter endpoint API `DELETE /recordings/{id}` (suppression logique ou physique).
- [ ] Ajouter endpoint upload audio `POST /upload` (multipart/form-data).
- [ ] Valider type MIME et taille max côté API.
- [ ] Stocker les fichiers audio dans `data/audio` avec nommage robuste (UUID).
- [ ] Gérer erreurs API standardisées (validation, not found, IO).
- [ ] Ajouter tests API (health/version + CRUD + upload).
- [ ] Mettre à jour Streamlit: formulaire upload + liste des enregistrements.
- [ ] Afficher statut upload + erreurs utilisateur dans Streamlit.
- [ ] Mettre à jour `README.md` (setup DB, endpoints, flux upload).
- [ ] Renforcer confidentialité: politique de conservation/suppression des audios.
