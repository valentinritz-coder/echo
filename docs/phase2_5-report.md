# Compte rendu — Phase 2.5 (robustesse mobile + Alembic)

## 1) Arborescence modifiée (<= 4 niveaux)

```text
.
├── docker-compose.yml
├── services
│   └── api
│       ├── alembic
│       │   ├── env.py
│       │   └── versions
│       │       └── 0001_init.py
│       ├── app
│       │   ├── db.py
│       │   ├── main.py
│       │   ├── models.py
│       │   └── settings.py
│       └── tests
│           └── test_entries.py
```

Fichiers modifiés depuis la phase 2 (`ae2cbaa..HEAD`) parmi ceux demandés:
- `services/api/app/main.py` ✅ modifié
- `services/api/app/settings.py` ➖ non modifié
- `services/api/app/models.py` ➖ non modifié
- `services/api/tests/test_entries.py` ✅ modifié
- `docker-compose.yml` ➖ non modifié

## 2) MIME audio — whitelist + mapping serveur

| MIME | Extension |
|---|---|
| `audio/mpeg` | `.mp3` |
| `audio/mp4` | `.m4a` |
| `audio/x-m4a` | `.m4a` |
| `audio/wav` | `.wav` |
| `audio/x-wav` | `.wav` |
| `audio/ogg` | `.ogg` |
| `audio/aac` | `.aac` |
| `audio/3gpp` | `.3gp` |
| `audio/3gpp2` | `.3g2` |
| `audio/webm` | `.webm` |
| `audio/aiff` | `.aiff` |

Formats mobiles explicitement présents:
- `audio/x-m4a` ✅
- `audio/webm` ✅
- `audio/3gpp` ✅
- `audio/aac` ✅
- `audio/x-wav` ✅

## 3) Flux upload réel (`POST /entries`)

Ordre d'exécution côté API:
1. Seed questions si nécessaire.
2. Vérifie que `question_id` existe (sinon 404).
3. Lit `audio_file.content_type`.
4. Valide le MIME via `ALLOWED_MIME_TYPES` (sinon 422 `unsupported_mime`).
5. Lit tout le fichier en mémoire (`await audio_file.read()`).
6. Valide la taille (`len(file_bytes) <= settings.max_upload_bytes`, sinon 413).
7. Génère un UUID v4 string (`entry_id`).
8. Résout extension via mapping MIME.
9. Construit `relative_path = Path("audio") / f"{entry_id}{ext}"`.
10. Construit `absolute_path = settings.data_dir / relative_path`.
11. Crée le dossier parent si nécessaire.
12. Écrit les octets sur disque (`write_bytes`).
13. Insère la ligne `Entry` en DB puis `commit` + `refresh`.

Format exact stocké en base pour `audio_path`:
- `audio/<uuid><extension>`
- Exemple: `audio/123e4567-e89b-12d3-a456-426614174000.m4a`

## 4) Tests ajoutés (`services/api/tests`)

Nouveaux tests MIME mobiles:
- `test_upload_accepts_audio_x_m4a`
- `test_upload_accepts_audio_webm`
- `test_upload_accepts_audio_3gpp`

MIME couverts par les tests:
- `audio/x-m4a`
- `audio/webm`
- `audio/3gpp`
- (déjà présent: rejet `text/plain`)

Résultat `pytest` observé:
- `6 passed, 2 warnings`

## 5) Base de données — point critique

Vérifications:
- `Base.metadata.create_all()` n'existe plus dans le code API.
- L'API démarre sans création automatique des tables.
- Si DB vide/non migrée: au startup, warning log
  - `Database not initialized. Run: alembic upgrade head`
- Ensuite, les endpoints touchant les tables échoueront tant que migration absente.

## 6) Alembic — cohérence

- Migration initiale `0001_init.py` présente et cohérente (tables `questions`, `entries`).
- Commande de référence: `alembic upgrade head`.
- Chemin DB Alembic (`sqlite:////app/data/echo.db`) aligné avec l'app (`DATA_DIR=/app/data` + `db.py`).

## 7) Docker + volumes

- Persistance audio: volume `./data:/app/data`.
- Répertoire conteneur audio: `/app/data/audio`.
- `settings.DATA_DIR` par défaut `/app/data` donc cohérent avec `docker-compose.yml`.

## 8) Risques restants (top 5)

1. MIME spoofing navigateur (basé sur `content_type` fourni client).
2. Extension dérivée du MIME et pas de signature binaire (fichier potentiellement incohérent).
3. Upload lu intégralement en mémoire (`read()`), risque RAM sur charge concurrente.
4. Course possible delete/read (fichier supprimé entre lookup DB et lecture).
5. DB non migrée: app up mais endpoints DB KO sans `alembic upgrade head`.

## 9) Checklist Phase 2.5 DONE

- Upload iPhone (`audio/x-m4a`) : couvert par test ✅
- Upload Android webm (`audio/webm`) : couvert par test ✅
- Fichier lisible après redémarrage Docker : architecture volume OK ✅
- `pytest` passe : oui (`6 passed`) ✅
- `alembic upgrade head` fonctionne : oui, avec répertoire DB existant ✅

## 10) Préparation Phase 3 (DB, IA) — champs à ajouter

- `transcript_text` (TEXT)
- `transcript_language` (VARCHAR)
- `transcript_confidence` (FLOAT)
- `summary_text` (TEXT)
- `sentiment_label` (VARCHAR)
- `sentiment_score` (FLOAT)
- `embedding_vector_ref` (VARCHAR / JSON selon stockage)
- `ai_model_name` (VARCHAR)
- `ai_model_version` (VARCHAR)
- `ai_processed_at` (DATETIME)
- `ai_status` (VARCHAR: pending/ok/error)
- `ai_error_message` (TEXT nullable)
