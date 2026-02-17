# echo-mvp

MVP "capsule de vie" — squelette technique uniquement (API FastAPI + front Streamlit + outillage local).

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

La page Streamlit tente automatiquement un appel `GET /health` vers l'API et affiche l'état.

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
│       ├── app/
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── settings.py
│       ├── Dockerfile
│       └── pyproject.toml
├── .env.example
├── .gitignore
├── docker-compose.yml
└── Makefile
```

## Commandes utiles

```bash
make setup   # crée .env si absent
make up      # lance api + web
make down    # stoppe les services
make logs    # logs en continu
```

## Portée de cette tâche

Inclus:
- squelette projet
- endpoints API `/health` et `/version`
- page Streamlit minimale avec check API
- docs produit + confidentialité

Exclu (volontairement):
- auth
- base de données
- upload audio
- transcription IA
