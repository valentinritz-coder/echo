# Compte rendu Phase 2 — echo-mvp (SQLite + upload audio)

## 1) Arborescence (profondeur <= 4)

```text
.
├── .env.example
├── Makefile
├── README.md
├── docker-compose.yml
├── apps/
│   └── web/
│       ├── Dockerfile
│       ├── app.py
│       └── pyproject.toml
└── services/
    └── api/
        ├── alembic/
        │   ├── env.py
        │   ├── script.py.mako
        │   └── versions/
        │       └── 0001_init.py
        ├── alembic.ini
        ├── app/
        │   ├── __init__.py
        │   ├── db.py
        │   ├── main.py
        │   ├── models.py
        │   ├── schemas.py
        │   └── settings.py
        └── tests/
            └── test_entries.py
```

## 2) Résumé précis des fichiers clés

### `services/api/app/main.py`
- Instancie FastAPI avec `title/version` issus des settings.
- Définit une whitelist MIME audio et 10 questions seed.
- `startup`: crée `data_dir` + `audio_dir`, puis `Base.metadata.create_all`.
- Error handlers JSON harmonisés:
  - `HTTPException` => `{error:{code,message}}`
  - `RequestValidationError` => code 422 avec `details`
  - exception générique => code 500 standardisé
- Routes:
  - `GET /health`
  - `GET /version`
  - `GET /questions/today` (seed auto + rotation déterministe via date)
  - `POST /entries` (multipart `user_id`, `question_id`, `audio_file`; validation MIME + taille; écriture disque + insertion DB)
  - `GET /entries?user_id=...`
  - `GET /entries/{entry_id}`
  - `GET /entries/{entry_id}/audio` (retourne `FileResponse`)
  - `DELETE /entries/{entry_id}` (supprime DB puis fichier)

### `services/api/app/settings.py`
- Variables d'env/settings (avec defaults):
  - `app_name="echo-mvp"`
  - `app_version="0.1.0"`
  - `app_env="development"`
  - `data_dir=Path("/app/data")`
  - `max_upload_size_mb=25`
- Chargement `.env` via `pydantic-settings`.
- Propriétés dérivées:
  - `max_upload_bytes = max_upload_size_mb * 1024 * 1024`
  - `audio_dir = data_dir / "audio"`

### `services/api/app/db.py`
- Déclare `Base = declarative_base()`.
- Crée engine SQLite pointant `sqlite:///{settings.data_dir/'echo.db'}` avec `check_same_thread=False`.
- Crée `SessionLocal` via `sessionmaker(autocommit=False, autoflush=False)`.
- Expose `get_db()` (generator) avec ouverture/fermeture de session.

### `services/api/app/models.py`
- `Question`:
  - table `questions`
  - `id` PK int indexé
  - `text`, `category` non-null
  - `is_active` bool non-null, défaut true
- `Entry`:
  - table `entries`
  - `id` PK string (UUID par défaut)
  - `user_id` string non-null indexé
  - `question_id` FK vers `questions.id` non-null
  - `audio_path`, `audio_mime` string non-null
  - `audio_size` int non-null
  - `created_at` datetime tz-aware, `server_default=now()`

### `alembic.ini`, `alembic/env.py`, migration initiale
- `alembic.ini`:
  - `script_location = alembic`
  - `sqlalchemy.url = sqlite:////app/data/echo.db`
- `alembic/env.py`:
  - charge config/logging
  - `target_metadata = Base.metadata`
  - importe modèles (`Entry`, `Question`) pour autogénération/metadata complète
  - gère online/offline migrations
- `alembic/versions/0001_init.py`:
  - crée table `questions` + index `ix_questions_id`
  - crée table `entries` + FK `question_id -> questions.id`
  - crée index `ix_entries_user_id`
  - downgrade inverse proprement l'ordre (drop index/table)

### `apps/web/app.py`
- UI Streamlit en 2 onglets: `Question du jour` et `Bibliothèque`.
- Lit `API_BASE_URL` (default `http://api:8000`) et `ALLOWED_TYPES` upload.
- Sidebar: saisie `user_id`, affichage endpoint API.
- Parcours utilisateur:
  - vérification santé API (`GET /health`)
  - récupération question (`GET /questions/today`)
  - upload multipart (`POST /entries`)
  - listing (`GET /entries?user_id=...`)
  - lecture audio (`GET /entries/{id}/audio` via `st.audio`)
  - suppression (`DELETE /entries/{id}` + rerun)
- Gestion erreurs API via extraction JSON homogène (`api_json_error`).

### `docker-compose.yml`
- Service `api`:
  - build `./services/api`
  - `env_file: .env`
  - env forcées: `APP_ENV`, `DATA_DIR=/app/data`
  - volume: `./data:/app/data`
  - port: `8000:8000`
- Service `web`:
  - build `./apps/web`
  - `env_file: .env`
  - env `API_BASE_URL=${API_BASE_URL:-http://api:8000}`
  - volume `./data:/app/data`
  - port `8501:8501`
  - `depends_on: api`

### `README.md` (commandes exactes)
- Démarrage Docker:
  - `cp .env.example .env`
  - `docker compose up --build`
- Migrations (depuis `services/api`):
  - `alembic upgrade head`
  - `alembic downgrade -1`
- Tests (depuis `services/api`):
  - `pip install -e ".[dev]"`
  - `pytest`

## 3) Cohérence chemins/volumes

- **Stockage audio host `data/audio`**: cohérent.
  - API écrit `audio/{uuid}.{ext}` sous `settings.data_dir`.
  - En docker, `DATA_DIR=/app/data` et volume `./data:/app/data` => persiste sur host dans `./data/audio`.
- **Persistance après redémarrage**: validée.
  - Test manuel: création d'entrée audio, arrêt API, redémarrage API, `GET /entries/{id}/audio` retourne `200`.
- **Web -> API via `API_BASE_URL` docker-compose**: cohérent.
  - Compose injecte `API_BASE_URL=${API_BASE_URL:-http://api:8000}` côté `web`.
  - L'app Streamlit lit `API_BASE_URL` et appelle cette base URL pour tous endpoints.

## 4) Checks exécutés

- `cd services/api && pytest`
  - Résultat final: `3 passed`.
- `cd services/api && python -c "import app.main; print('ok')"`
  - Import OK.
- `curl http://127.0.0.1:8000/health`
  - `{"status":"ok"}`.
- `curl http://127.0.0.1:8000/questions/today`
  - Réponse 200 avec question seed.

## 5) Top 10 risques / bugs probables + reproduction

1. **MIME iOS/Android non couvert** (`audio/aac`, `audio/3gpp`, `audio/webm`, etc.)
   - Repro: uploader un fichier dont `content-type` n'est pas dans la whitelist => `422 Unsupported audio MIME type`.
2. **Validation MIME basée sur en-tête client** (contournable)
   - Repro: forger multipart `type=audio/mpeg` avec payload non audio => accepté.
3. **Incohérence extension/MIME**
   - Repro: envoyer `type=audio/mpeg` avec nom `voice.wav` => extension server forcée `mp3`; confusion possible côté debug.
4. **Limite taille en RAM** (lecture complète en mémoire)
   - Repro: upload proche de 25MB en parallèle x N requêtes => pression mémoire process.
5. **Course condition suppression/lecture**
   - Repro: lancer `GET /entries/{id}/audio` pendant `DELETE /entries/{id}` => intermittence 404.
6. **Orphelins fichiers si crash entre write disque et commit DB**
   - Repro: simuler crash après `write_bytes` avant `db.commit` => fichier présent sans entrée DB.
7. **Orphelins DB si crash après commit avant unlink delete**
   - Repro: simuler crash juste après commit delete et avant `unlink` => entrée supprimée, fichier restant.
8. **`Base.metadata.create_all` + Alembic en parallèle**
   - Repro: démarrage auto-create puis migrations manuelles divergentes => drift schéma potentielle.
9. **Timezone SQLite sur `created_at`**
   - Repro: comparer tri/format timezone entre environnements => comportement non strictement homogène.
10. **Deprecation FastAPI `@app.on_event("startup")`**
   - Repro: exécuter tests => warning; futur upgrade FastAPI peut casser sans migration vers lifespan.

## 6) Checklist “Phase 2 DONE” (critères vérifiables)

- [ ] Lancer local sans Docker (`uvicorn app.main:app`) + `/health` OK
- [ ] Lancer Docker (`docker compose up --build`) + API/Web accessibles
- [ ] Upload audio OK (MIME autorisé, <=25MB)
- [ ] Lecture audio OK (`GET /entries/{id}/audio` + Streamlit)
- [ ] Suppression OK (DB + fichier supprimés)
- [ ] Redémarrage conserve la bibliothèque (DB SQLite + fichiers audio persistants)
- [ ] Tests API verts (`pytest`)
- [ ] Migrations Alembic applicables (`upgrade/downgrade`)

## 7) Checklist “Phase 3” (IA transcription + résumé + tags)

1. Définir contrat de réponse enrichie (`transcript`, `summary`, `tags`, `confidence`, `language`).
2. Ajouter colonnes SQLAlchemy + migration Alembic pour métadonnées IA.
3. Implémenter pipeline asynchrone (queue/background task) post-upload.
4. Intégrer provider STT (OpenAI/Whisper ou équivalent) avec retries/timeouts.
5. Ajouter fallback en cas d'échec IA (entrée disponible sans blocage UX).
6. Versionner prompts de résumé/tagging + tests de non-régression.
7. Exposer statut de traitement (`pending/processing/done/failed`) côté API.
8. Mettre à jour UI Streamlit pour afficher progression + erreurs IA.
9. Ajouter limites/coûts (durée max audio, quota utilisateur, rate limit).
10. Ajouter observabilité (logs structurés, métriques latence, taux d'échec, coûts).
11. Renforcer confidentialité (PII scrubbing, politique rétention, suppression définitive).
