## Résumé exécutif
Le dépôt fournit un MVP cohérent **API FastAPI + UI Streamlit** avec persistance locale SQLite et fichiers audio sur disque, orchestré par Docker Compose. L’API est fonctionnelle et testée (9 tests passent) mais reste sur un socle “MVP”: pas d’authentification, pas d’autorisation, pas de versioning d’API, pas de pagination, pas de rate limiting, pas de workers IA. Les migrations Alembic existent et couvrent le schéma principal + “AI plumbing”, ce qui est un bon point. Le stockage audio est simple et lisible, avec limite de taille et whitelist MIME, mais l’upload charge tout en mémoire et ne fait pas de validation de contenu réel. Les erreurs sont harmonisées côté JSON, mais l’observabilité est minimale (pas de logs structurés/correlation-id/health DB/readiness). Côté sécurité, pas de secrets committés détectés, mais CORS/headers/scope ACL ne sont pas implémentés.  
Conclusion: base saine pour itérer vite, mais **non prête production** sans renforcement sécurité/data/ops.

---

## Tableau synthèse — Constat / Impact / Reco / Priorité / Effort

| Constat | Impact | Reco | Priorité | Effort |
|---|---|---|---|---|
| Pas d’auth/ACL backend (user_id libre en query/form) | Exposition/lecture/suppression inter-utilisateurs triviale | Ajouter JWT + dépendance `Depends(get_current_user)` + filtrage propriétaire | Critique | Moyen |
| API non versionnée (`/v1` absent) | Évolutions cassantes côté clients | Introduire routeur versionné (`/api/v1`) | Haute | Faible |
| `GET /entries` sans pagination/limit | Risque perf/mémoire à l’échelle | `limit/offset`, tri, filtres, index adaptés | Haute | Faible |
| Upload audio lit le fichier entier en RAM | Pics mémoire et DoS simple | Streaming/chunked write + quotas | Haute | Moyen |
| Pas de CORS/headers sécurité/rate limiting | Surface d’attaque API exposée | CORS strict, `TrustedHost`, security headers, limiter | Haute | Moyen |
| Observabilité minimale | Débogage incident difficile | Logs JSON + request-id + métriques + health/readiness DB | Haute | Moyen |
| SQLite local + volume unique | Concurrence limitée / résilience faible | Plan migration Postgres managé | Haute | Élevé |
| Pas de backup/restoration formalisé | Risque perte irréversible | Politique backup DB+audio + test restore | Critique | Moyen |
| Concept WORM/immutabilité non implémenté | Capsules modifiables/supprimables | État “frozen” + contraintes DB + blocage API | Haute | Moyen |
| AI “plumbing” sans worker | États `pending` potentiellement bloqués | File de jobs + worker idempotent + retries | Moyenne | Moyen |

---

## 1) Inventaire & cartographie

### Arborescence utile (dossiers clés)
- `services/api/app`: backend FastAPI (entrée app, modèles, schémas, DB, settings, utilitaires IA).
- `services/api/alembic` + `services/api/alembic.ini`: migrations DB Alembic (env + versions).
- `services/api/tests`: tests API (CRUD, MIME, endpoints IA de base).
- `apps/web`: UI Streamlit consommant l’API via HTTP requests.
- `data/audio`: stockage local audio versionné via `.gitkeep` (données runtime via volume).

### Points d’entrée identifiés
- **App FastAPI**: `services/api/app/main.py` (objet `app = FastAPI(...)`).
- **Service API runtime**: `uvicorn app.main:app` via Dockerfile API.
- **UI Streamlit**: `streamlit run app.py` via Dockerfile web.
- **Migrations**: Alembic (`alembic upgrade head`).
- **Workers**: **inconnu / non trouvé** (doc indique explicitement “No worker”).

### Dépendances (et usage)
- API: FastAPI, Uvicorn, pydantic-settings, SQLAlchemy, Alembic, python-multipart; dev: pytest/httpx.
- Web: Streamlit + requests.

---

## 2) Architecture backend (qualité du socle)

- Structure présente mais **pas en couches nettes**: routes, logique métier, I/O fichier et accès DB sont dans `main.py` (pas de services/repositories séparés).
- Couplage métier/infra: logique upload + écriture disque + transaction DB directement dans endpoint `POST /entries`.
- Couplage UI/auth simplifiée: `user_id` manipulé côté UI et transmis tel quel au backend, sans identité serveur.
- Config: centralisée avec `BaseSettings` (`.env`, `DATA_DIR`, taille max upload). C’est bon pour la base MVP.

---

## 3) API

### Endpoints existants (groupés)
- **System**: `GET /health`, `GET /version`.
- **Questions**: `GET /questions/today`.
- **Entries**: `POST /entries`, `GET /entries`, `GET /entries/{id}`, `GET /entries/{id}/audio`, `DELETE /entries/{id}`.
- **AI metadata/runs**: `POST /entries/{id}/ai/process`, `GET /entries/{id}/ai`, `GET /ai/runs/{run_id}`.

### Évaluation API
- Versioning: **absent** (`/v1` non trouvé).
- REST cohérence: globalement correcte (ressources `entries`, `questions`), mais `GET /entries` impose `user_id` query sans auth réelle.
- Validation: bonne base (Pydantic schemas + validation erreurs + MIME + taille).
- Gestion erreurs: handlers uniformisés `HTTPException`, `RequestValidationError`, `Exception`.
- Pagination/filtres: pagination absente, filtre unique par `user_id`.
- OpenAPI/docs: FastAPI auto disponible (non désactivée), mais pas de tags/exemples détaillés custom dans les routes.

---

## 4) Données & migrations

### Schéma DB (tables/relations)
- `questions`: id, text, category, is_active (NOT NULL).
- `entries`: FK vers `questions`, metadata audio, created_at, plus champs IA ajoutés en v2 (status/run/hash/duration).
- `ai_runs`: FK `entry_id` vers `entries` avec `ondelete=CASCADE`, metadata pipeline/outputs/errors.

### Contraintes/index/intégrité
- CHECK sur statuts `entries.ai_status` et `ai_runs.status`.
- FK `entries.ai_last_run_id -> ai_runs.id` (`SET NULL`).
- Index présents: `ix_entries_user_id`, `ix_ai_runs_entry_id`, `ix_ai_runs_status_requested_at`.
- `UNIQUE` métier absents (ex: duplication user/question/date). **inconnu / non trouvé**.

### Migrations Alembic
- Chaîne de migration simple et reproductible (`0001` -> `0002`).
- `env.py` force l’URL SQLite depuis `DATA_DIR`, utile local/docker.

---

## 5) Stockage audio / fichiers

- Stockage assets: **filesystem local** `DATA_DIR/audio/{uuid}.{ext}`.
- Upload:
  - taille max 25MB via setting (`max_upload_size_mb`).
  - whitelist MIME côté backend (`ALLOWED_MIME_TYPES`).
  - **pas de streaming** (lecture complète en RAM `await audio_file.read()`).
  - reprise/idempotence: **inconnu / non trouvé**.
  - hash: SHA256 utilisé pour pipeline IA (pas pour dédup upload).
- Sécurité fichiers:
  - pas de path user direct (path généré serveur, limite traversal).
  - accès non autorisé: possible car route audio non protégée par auth (ID suffit).
  - URL signée: **inconnu / non trouvé**.

---

## 6) Auth & contrôle d’accès

- Système d’auth backend: **absent / non trouvé** (pas de JWT, session, OAuth, dependency security).
- Contrôle d’accès: **absent**; l’API se base sur `user_id` fourni client en query/form. 
- Secrets: variable `OPENAI_API_KEY` prévue mais non exploitée dans backend actuel.
- Cas “consultation mémoire” (invitation/token viewer/magic link): **inconnu / non trouvé**.

---

## 7) État “mémoire” (WORM)

- Concept de capsule figée/immutable: **inconnu / non trouvé** (pas de flag `frozen`, pas de verrou métier, suppression autorisée).
- Risque: un enregistrement peut être supprimé à tout moment via endpoint public si ID connu.

---

## 8) Observabilité & robustesse

- Logs: usage minimal (`logger.warning` startup), config Alembic basique textuelle. Pas de logs structurés JSON.
- Correlation-id: **inconnu / non trouvé**.
- Erreurs: handlers uniformes; générique masque détails (bon pour prod), mais pas de traçage central visible.
- Healthchecks: `GET /health` présent, mais pas de readiness DB dédiée.
- Rate limiting/protection abusive: **inconnu / non trouvé**.

---

## 9) Sécurité (minimum viable security)

- Secrets en clair committés: aucun secret renseigné trouvé; `.env.example` contient placeholders.
- CORS: middleware CORS non trouvé.
- CSRF: non applicable en l’état (pas de sessions/cookies backend), mais auth future à cadrer.
- Headers sécurité (`HSTS`, `X-Content-Type-Options`, etc.): **inconnu / non trouvé**.
- Scan vulnérabilités dépendances: non exécuté ici (à faire via `pip-audit`/`safety`) — **inconnu / non trouvé**.

---

## 10) Tests & qualité

- Tests présents: API integration-ish avec TestClient + Alembic sur DB temporaire.
- Couverture fonctionnelle: CRUD entries, MIME, endpoints IA de base.
- Couverture approximative: **inconnu / non trouvé** (pas de rapport coverage observé).
- Qualité statique (ruff/black/mypy): **inconnu / non trouvé** (pas de config visible).
- CI: **inconnu / non trouvé** (pas de workflow CI repéré dans les fichiers listés).

---

## 11) Docker & déploiement

- Dockerfiles séparés API/Web, simples et reproductibles localement.
- Compose unique dev: `docker compose up --build` + volume `./data:/app/data`.
- Dev/prod séparation: faible (même images/profils, pas de compose prod dédié). **inconnu / non trouvé**.
- Persistance:
  - DB SQLite dans volume `data`.
  - audios sous `data/audio`.
- Backups: **inconnu / non trouvé** (aucune stratégie explicite).

---

## 12) Dette technique & risques (Top 10)

1. **Absence auth/ACL** (critique sécurité).  
2. **Suppression non protégée** des entrées/audio par ID. 
3. **Upload RAM-bound** (DoS/perf). 
4. **Pas de pagination** (scalabilité lecture). 
5. **Pas de rate limiting/CORS durci**. 
6. **SQLite local** (concurrence/HA limitée). 
7. **Pas de backup/restore formalisé**. 
8. **Pas de WORM** (capsule mutable/supprimable). 
9. **AI pending sans worker** (états bloqués potentiels). 
10. **Observabilité insuffisante** en incident (trace distribuée absente). 

### Quick wins (≤1h)
- Préfixer routes via `/api/v1`.
- Ajouter `limit/offset` à `GET /entries`.
- Ajouter dépendance auth “stub” + interdire opérations cross-user.
- Ajouter endpoint readiness DB.

### Medium (1–2 jours)
- JWT access/refresh + permissions par ressource.
- Middleware request-id + logs JSON.
- Upload streaming + validation stricte MIME/extension.
- Rate limiting basique + CORS strict configurable.

### Big rocks (1–2 semaines)
- Migration Postgres + adaptation Alembic.
- Worker asynchrone IA (RQ/Celery/Arq) idempotent + retries.
- Politique backups (DB+audio) + procédures de restore testées.
- WORM robuste (flag frozen + audit trail).

---

## 13) Plan d’action (3 phases)

### A) Stabiliser backend (data + API + auth + storage)
1. Introduire `/api/v1` + contrats de réponse homogènes versionnés.  
2. Implémenter auth JWT (access/refresh) + `current_user` côté routes.  
3. Verrouiller ACL sur entries/audio (ownership server-side, pas par `user_id` client).  
4. Ajouter pagination/filtrage/tri sur listings.  
5. Refactor upload en streaming + anti-abus (taille, type, quotas).  
6. Ajouter état WORM minimal (`is_frozen`) et blocage DELETE/UPDATE.

### B) Fiabiliser (tests + observabilité + backups + workers)
1. Étendre tests: auth, ACL, cas concurrents, erreurs fichiers.  
2. Ajouter coverage + lint/format/type-check en CI.  
3. Mettre logs structurés + request-id + métriques (latence/erreurs).  
4. Ajouter readiness check DB + alertes de base.  
5. Implémenter backups auto + test restore périodique.  
6. Introduire worker IA réel (queue + retries + DLQ).

### C) Préparer long-terme (S3, Postgres, export, WORM renforcé)
1. Basculer stockage audio vers S3/MinIO (URLs signées).  
2. Migrer SQLite -> Postgres (index/transactions/locks adaptés).  
3. Ajouter export utilisateur (audio+metadata) et suppression RGPD-like.  
4. Renforcer WORM: journal d’audit, hash chaîné/preuve d’intégrité, politique rétention.

---

## Questions ouvertes
1. Quel modèle d’identité cible (email+mot de passe, OAuth, magic link) ?  
2. Le besoin “consultation mémoire” doit-il être public, invité, ou strictement propriétaire ?  
3. Exigences légales (RGPD, droit à l’oubli, rétention) ?  
4. SLA cible (RPO/RTO) pour dimensionner backups ?  
5. Volume attendu (uploads/jour, durée moyenne audio) ?  
6. Priorité produit: IA rapide vs robustesse sécurité ?  
7. Besoin de chiffrement at-rest pour les audios ?  
8. WORM attendu “soft” applicatif ou “hard” (immutabilité forte) ?
