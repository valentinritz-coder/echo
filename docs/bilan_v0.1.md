# Bilan de release v0.1 — echo-mvp

## Périmètre du lot clôturé

Lot clôturé côté API/infra:
- Authentification JWT (access + refresh) et comptes utilisateurs.
- ACL sur les ressources `entries` (isolation stricte par utilisateur).
- Pagination/tri sur la liste des entrées.
- Upload audio en streaming, contrôle signature, hash SHA-256, limite de taille.
- `X-Request-Id` + logs JSON structurés.
- Endpoints de santé `/health` et readiness `/readyz`.
- Scripts de backup/restore (SQLite + audio) avec garde-fous de sécurité.
- WORM applicatif: gel d’une entrée (`freeze`) puis suppression interdite.
- Stabilisation migrations Alembic + base de tests pytest + E2E opt-in.

---

## Ce qui est livré (vue utilisateur)

- Un utilisateur authentifié peut se connecter (`/auth/login`) puis rafraîchir son token (`/auth/refresh`) pour rester connecté sans ressaisie immédiate du mot de passe.
- Les entrées audio sont privées: un utilisateur ne peut ni lire, ni télécharger, ni supprimer les entrées d’un autre utilisateur (retour `403`).
- L’upload audio accepte plusieurs formats (mp3, m4a/mp4, wav, ogg, aac, 3gpp, webm, aiff), avec refus explicite des fichiers invalides (MIME/signature/extension) et des fichiers trop volumineux (`413`).
- La bibliothèque est paginée (paramètres `limit`, `offset`, `sort`) pour garder des temps de réponse stables quand le volume d’entrées augmente.
- Une entrée peut être « gelée » via `POST /entries/{id}/freeze`; ensuite sa suppression via `DELETE /entries/{id}` est bloquée (`409`).
- L’état de la plateforme est vérifiable via `/api/v1/health` (liveness) et `/api/v1/readyz` (DB + répertoire audio réellement utilisable).

## Ce qui est livré (vue technique)

- Middleware `RequestIdMiddleware` injectant/normalisant `X-Request-Id` et journalisation JSON (`method`, `path`, `status_code`, `duration_ms`, `query_keys`).
- Upload streaming avec écriture atomique via fichier temporaire + `os.replace`, calcul SHA-256 au fil de l’eau, et extraction optionnelle de durée WAV.
- Validation upload en couches: MIME autorisé, extension cohérente, signature binaire conforme au type attendu.
- Schéma DB enrichi via Alembic: utilisateurs + FK, index de pagination, métadonnées audio (`audio_sha256`, `audio_duration_ms`), drapeau de gel (`is_frozen`).
- Vérification au startup de l’état DB (warning explicite si migrations non appliquées).
- Couverture de tests: auth, ACL, upload, pagination, freeze, endpoints système, sécurité HTTP, et scénarios E2E.

---

## Endpoints importants et comportement

- `POST /api/v1/auth/login`  
  Authentifie un utilisateur actif (email/mot de passe) et retourne `{access_token, refresh_token, token_type}`; sinon `401 invalid_credentials`.

- `POST /api/v1/auth/refresh`  
  Prend un `refresh_token`, vérifie le type/validité/utilisateur actif, et retourne un nouveau `access_token`; sinon `401`.

- `GET /api/v1/health`  
  Liveness simple: répond `200 {"status":"ok"}` si l’API répond.

- `GET /api/v1/readyz`  
  Readiness opérationnelle: teste `SELECT 1` DB + création/écriture/suppression d’un fichier sonde dans `audio_dir`; renvoie `200` si tout est OK, sinon `503` avec détail des checks.

- `GET /api/v1/version`  
  Retourne le nom/version applicatifs exposés par la configuration.

- `GET /api/v1/questions/today`  
  Nécessite JWT; seed les questions si besoin, puis retourne la question active du jour (rotation déterministe), sinon `404` si aucune active.

- `POST /api/v1/entries`  
  Nécessite JWT; upload multipart (`question_id`, `audio_file`) validé en streaming (MIME/signature/taille), persiste le fichier et crée l’entrée avec `audio_size`, `audio_sha256`, `audio_duration_ms`.

- `GET /api/v1/entries`  
  Nécessite JWT; liste uniquement les entrées de l’utilisateur courant avec pagination (`limit` plafonné à 200, `offset`) et tri (`created_at_*`, `id_*`).

- `GET /api/v1/entries/{id}`  
  Nécessite JWT; retourne l’entrée si elle existe et appartient à l’utilisateur, sinon `404` ou `403`.

- `GET /api/v1/entries/{id}/audio`  
  Nécessite JWT; renvoie le binaire audio (`FileResponse`) si la ressource existe et est autorisée, sinon `404`/`403`.

- `POST /api/v1/entries/{id}/freeze`  
  Nécessite JWT; positionne `is_frozen=true` de manière idempotente et retourne `{"status":"frozen", ...}`.

- `DELETE /api/v1/entries/{id}`  
  Nécessite JWT; supprime entrée + fichier audio si autorisé, mais retourne `409 {code:"frozen"}` si l’entrée est gelée.

---

## Changements DB / migrations

Chaîne de migrations Alembic livrée:

1. `0001_init`  
   Crée `questions` et `entries` (champs initiaux audio + `created_at`).

2. `0002_users_and_auth`  
   Crée `users`, ajoute la contrainte FK `entries.user_id -> users.id`, et migre les entrées legacy vers un utilisateur technique `legacy` si nécessaire.

3. `0003_entries_list_indexes`  
   Ajoute l’index composite `ix_entries_user_id_created_at_id` pour la pagination/tri des listes.

4. `0004_entry_audio_metadata`  
   Ajoute les colonnes:
   - `audio_sha256` (`String(64)`, non nul, valeur par défaut initiale),
   - `audio_duration_ms` (`Integer`, nullable).

5. `0005_entry_freeze_flag`  
   Ajoute la colonne `is_frozen` (`Boolean`, non nul, défaut `0`) pour le comportement WORM applicatif.

---

## Procédure de test

> Commandes à exécuter depuis la racine du repo, sauf mention contraire.

### Qualité code (lint/format)

```bash
ruff check .
ruff format --check .
```

### Tests unitaires / intégration API

```bash
cd services/api && pytest
```

### Tests E2E (opt-in)

```bash
cd services/api && pytest -m e2e
```

Pré-requis E2E: stack API démarrée + DB migrée + users de test disponibles (cf. fixtures `tests_e2e`).

### Smoke test readiness

```bash
curl -i http://localhost:8000/api/v1/readyz
```

Attendu: `HTTP/1.1 200` et payload avec `status: "ok"`, `checks.db.ok: true`, `checks.audio_dir.ok: true`.

---

## Ops

### Backup / restore (SQLite + audio)

- Backup standard:

```bash
scripts/backup.sh
```

- Exemples utiles:

```bash
scripts/backup.sh --data-dir ./data --out-dir ./backups
scripts/backup.sh --db ./data/echo.db --audio-dir ./data/audio
```

- Restore vers dossier de restauration isolé:

```bash
scripts/restore.sh backups/echo_backup_YYYYmmdd_HHMMSSZ.tar.gz
scripts/restore.sh backups/echo_backup_YYYYmmdd_HHMMSSZ.tar.gz --dest-dir ./data_restore
```

### Safety intégrée

- `backup.sh` privilégie `sqlite3 .backup` si disponible (snapshot cohérent), sinon fallback copie fichier DB.
- `restore.sh` refuse les chemins d’archive dangereux (absolus / `..`).
- Restauration non destructive: extraction dans un sous-répertoire dédié; en non-interactif, échec explicite si la cible existe déjà.

### WORM (gel d’entrée)

- Geler une entrée:

```bash
curl -X POST -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/api/v1/entries/<ENTRY_ID>/freeze
```

- Après gel, toute tentative de suppression:

```bash
curl -X DELETE -H "Authorization: Bearer <TOKEN>" \
  http://localhost:8000/api/v1/entries/<ENTRY_ID>
```

retourne `409` avec code d’erreur `frozen`.

---

## Known issues / warnings

- **Avertissement passlib/bcrypt déprécié** observé en tests (`CryptContext(..., deprecated="auto")` + backend bcrypt):
  - Impact: bruit dans les logs/tests, pas de blocage fonctionnel immédiat.
  - Reco: planifier migration contrôlée de stratégie hash (ex. Argon2id ou bcrypt sans composants dépréciés), avec compatibilité de vérification des hashes existants.

- **Dépréciation FastAPI `@app.on_event("startup")`**:
  - Impact: warning de framework; risque de casse à moyen terme lors de montée de version.
  - Reco: migrer vers le mécanisme `lifespan` FastAPI et déplacer l’initialisation (logging, vérifs DB, seed admin) dans ce cycle.

---

## Next steps (priorisés)

1. **Migrer `startup` vers `lifespan`** pour supprimer la dette de dépréciation framework.
2. **Finaliser la stratégie de hash password** (cible unique, migration progressive, tests de rétrocompatibilité).
3. **Ajouter observabilité métier** (compteurs d’upload acceptés/rejetés, latence par endpoint, taux `4xx/5xx`).
4. **Renforcer WORM** (audit trail immuable des opérations `freeze`/`delete`, horodatage et acteur).
5. **Automatiser un pipeline CI minimal** (`ruff`, `pytest`, smoke `/readyz`) avec seuils de blocage.
