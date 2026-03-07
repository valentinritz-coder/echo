# Echo MVP — Audit fonctionnalités "Souvenir multimédia"

## 0) Contexte et périmètre
- **Scope analysé**: backend FastAPI (`services/api`) + front web statique (`apps/web-static`) + front Streamlit (`apps/web`) pour l'état réel des fonctionnalités audio/texte/images autour des entries.
- **Hors scope**: implémentation d'un nouveau design, correctifs, migrations additionnelles, optimisation UX, infra prod.
- **Hypothèses**:
  - Les formats audio produits navigateur (souvent `audio/webm`/`audio/ogg` selon UA) sont potentiellement acceptés côté API si MIME + signature/extension sont cohérents.
  - Le front statique est une UI MVP de démonstration (pas encore branchée API) malgré des composants présents.
  - Le front Streamlit est actuellement le client réellement connecté à l'API pour créer/lire des entries audio.

## 1) Cartographie rapide du repo

### Backend (services/api)
- **Points d'entrée (routes)**
  - Dans `app/main.py`: `GET /api/v1/version`, `GET /api/v1/questions/today`, `POST /api/v1/entries`, `GET /api/v1/entries`, `GET /api/v1/entries/{entry_id}`, `PATCH /api/v1/entries/{entry_id}`, `POST /api/v1/entries/{entry_id}/freeze`, `GET /api/v1/entries/{entry_id}/audio`, `POST /api/v1/entries/{entry_id}/audio`, `DELETE /api/v1/entries/{entry_id}/audio`, `DELETE /api/v1/entries/{entry_id}`, `POST /api/v1/entries/{entry_id}/assets`, `GET /api/v1/entries/{entry_id}/assets`, `GET /api/v1/assets/{asset_id}` (download).
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh` dans `app/routes/auth.py`.
  - `GET /api/v1/health`, `GET /api/v1/readyz` dans `app/routes/system.py`.
- **Modèles DB pertinents (entries/users/assets)**
  - `users`, `questions`, `entries`, `entry_assets` existent.
  - `entries` contient: `id`, `user_id`, `question_id`, `audio_path`, `audio_mime`, `audio_size`, `audio_sha256`, `audio_duration_ms`, `text_content`, `is_frozen`, `created_at` (champs audio et texte optionnels).
  - `entry_assets`: `id`, `entry_id`, `user_id`, `asset_type`, `path`, `mime`, `size`, `sha256`, `width`, `height`, `created_at` (usage actuel: images).
- **Stockage fichiers (audio/images)**
  - Audio: `DATA_DIR/audio/<uuid>.<ext>`.
  - Images: `DATA_DIR/images/` (chemins dans `entry_assets.path`).
  - Readiness: check `audio_dir` en écriture (pas de check dédié images_dir).
- **Sécurité (JWT, ACL, freeze/WORM)**
  - JWT access/refresh via `/auth/login` et `/auth/refresh`.
  - ACL propriétaire sur entry, audio, assets (GET/POST/delete), freeze.
  - Freeze (`is_frozen`) bloque la suppression (409), proche logique WORM sur delete entry.

### Frontend (apps/web-static)
- **Pages/JS existants**
  - `index.html` inclut composer avec `textarea`, bouton micro, input images multiple, submit.
  - `app.js` gère autosize texte, preview images locale, enregistrement micro `MediaRecorder` + preview audio.
- **Appels API existants**
  - Aucun `fetch()`/appel `/api/v1` dans `apps/web-static/app.js`.
- **UI existante liée aux entries**
  - Sidebar timeline alimentée par données fake (`memories` hardcodées).
  - Pas de chargement des entries API ni rendu réel d'une entry serveur.

## 2) État des fonctionnalités (tableau)

| Feature | Status (OK/Partiel/Absent) | Preuves (fichiers + lignes/fonctions) | Gaps | Notes/risques |
|---|---|---|---|---|
| Upload audio (déjà) + endpoints de download | **OK** | `POST /entries` (multipart `question_id` + `audio_file`) et stockage disque; `GET /entries/{id}/audio` renvoie `FileResponse`. | Pas d'endpoint audio public/signé; download seulement via auth user propriétaire. | Solide pour audio seul; bien cadré ACL + MIME. |
| Record micro depuis web (`getUserMedia`/`MediaRecorder`) | **Partiel** | `apps/web-static/app.js` implémente `getUserMedia`, `MediaRecorder`, création `Blob`, preview `<audio>`. | Pas d'upload API du blob enregistré; pas d'assemblage multipart; pas de chunk upload. | UX micro existe mais non persistée backend. |
| Texte entry (création + retrieval) | **OK** | `Entry.text_content` (nullable); `POST /entries` accepte `text`/`text_content` (form), `PATCH /entries/{id}`; `EntryOut` expose `text_content`; validation `MAX_TEXT_CHARS`. | - | Texte seul ou avec audio. |
| Upload images (1..n) + metadata + download | **OK** | `POST /entries/{id}/assets`, table `entry_assets`, `GET /entries/{id}/assets`, `GET /assets/{id}` (download), MIME/signature/dimensions; listing entry inclut `assets` avec `download_url`. | Limite nombre images par entry. | ACL propriétaire. |
| Listing entries (pagination/tri) et si assets apparaissent ou non | **OK** | `GET /entries` avec `limit/offset/sort`; `EntryOut` inclut `text_content`, `audio_url`, `assets` (download_url). | - | Projection multimédia cohérente. |
| ACL (cross-user) sur entry + audio + images | **OK** | ACL propriétaire sur entry, audio, assets (upload/download), delete, freeze; tests ACL cross-user. | - | Couvert. |
| Freeze/WORM impact (modif/suppression) | **OK** | `POST /entries/{id}/freeze`; freeze bloque DELETE entry et modification/upload (entry + assets); tests freeze. | - | Freeze couvre entry et assets. |
| Validations MIME/signature (audio, images) | **OK** | Audio: whitelist MIME + signature + extension + taille (`storage.py`). Images: MIME image + signature + dimensions dans upload assets. | - | Contrôles en place. |
| Limites de taille / env vars | **Partiel** | `max_upload_size_mb` (audio), `max_upload_image_mb`, `max_text_chars`; appliqués. | Limite nombre images par entry; pas de quotas globaux. | Dimensionnement audio/image/texte pris en charge. |

## 3) Endpoints/API actuels (inventaire)
- **System**
  - `GET /api/v1/health` → `{status:"ok"}`
  - `GET /api/v1/readyz` → `{status, checks:{db,audio_dir}}`
  - `GET /api/v1/version` → `{name,version}`
- **Auth**
  - `POST /api/v1/auth/login` (JSON: `email`, `password`) → `{access_token, refresh_token, token_type}`
  - `POST /api/v1/auth/refresh` (JSON: `refresh_token`) → `{access_token, token_type}`
- **Entries / Questions**
  - `GET /api/v1/questions/today` (Bearer) → `QuestionOut{id,text,category,is_active}`
  - `POST /api/v1/entries` (Bearer, multipart): `question_id` (form), `text`/`text_content` (form optionnel), `audio_file` (file optionnel); réponse: `EntryOut` (avec `text_content`, `audio_url`, `assets`). Au moins texte ou audio requis.
  - `GET /api/v1/entries` (Bearer, query): `limit`, `offset`, `sort in [created_at_desc, created_at_asc, id_asc, id_desc]` → `{items,next_offset,limit,offset}`
  - `GET /api/v1/entries/{entry_id}` (Bearer) → `EntryOut`
  - `PATCH /api/v1/entries/{entry_id}` (Bearer, JSON: `question_id`, `text_content` optionnels) → `EntryOut`
  - `GET /api/v1/entries/{entry_id}/audio` (Bearer) → binaire audio (`FileResponse`) ou 404 si entry sans audio
  - `POST /api/v1/entries/{entry_id}/audio` (Bearer, multipart) → ajout/remplacement audio, `EntryOut`
  - `DELETE /api/v1/entries/{entry_id}/audio` (Bearer) → `{status:"audio_deleted",id}`
  - `POST /api/v1/entries/{entry_id}/freeze` (Bearer) → `{status:"frozen",id,is_frozen:true}`
  - `DELETE /api/v1/entries/{entry_id}` (Bearer) → `{status:"deleted",id}` ou 409 si frozen
  - `POST /api/v1/entries/{entry_id}/assets` (Bearer, multipart image) → `EntryAssetOut`
  - `GET /api/v1/entries/{entry_id}/assets` (Bearer) → liste `EntryAssetOut` (avec `download_url`)
  - `GET /api/v1/assets/{asset_id}` (Bearer) → binaire image (`FileResponse`)

## 4) DB / migrations
- **Schéma actuel pertinent**
  - `questions` créée en 0001.
  - `entries` créée en 0001 avec audio de base; 0002 `user_id`; 0004 `audio_sha256`, `audio_duration_ms`; 0005 `is_frozen`; 0006 `text_content`; 0008 champs audio optionnels (nullable).
  - `entry_assets` créée en 0007 (`id`, `entry_id`, `user_id`, `asset_type`, `path`, `mime`, `size`, `sha256`, `width`, `height`, `created_at`).
- **Index existants**
  - `ix_entries_user_id` (0001), `ix_entries_user_id_created_at_id` (0003), `ix_users_email`, `ix_questions_id`.
- **État actuel**
  - Texte et assets images couverts par le schéma; pas d'index dédié assets au-delà des FK.

## 5) Frontend: capacités actuelles
- **MediaRecorder / input file / textarea**
  - `apps/web-static`: oui pour les trois (textarea, micro, images input multiple) mais uniquement côté UI locale.
  - `apps/web` (Streamlit): pas de MediaRecorder navigateur; upload fichier audio manuel via `file_uploader`.
- **Flux exact actuel pour créer une entry (Streamlit / API)**
  1. Login via `/auth/login`.
  2. Récupération question via `/questions/today`.
  3. Création: `POST /entries` avec `question_id` et optionnellement `text`/`text_content` et/ou `audio_file`. Ajout audio différé possible via `POST /entries/{id}/audio`. Images via `POST /entries/{id}/assets`.
  4. Listing `/entries`, détail `GET /entries/{id}` (texte, `audio_url`, `assets`), lecture audio via `GET /entries/{id}/audio`, téléchargement images via `GET /assets/{id}`.
- **Ce qui manque**
  - `web-static`: pas de submit branché API (pas de `fetch`), donc ni texte ni images ni audio micro persistés.
  - `web` (Streamlit): champ texte et upload images supportés par l'API; à vérifier côté UI selon version.
  - Backend: texte, images (assets), audio optionnel sont en place.

## 6) Gaps prioritaires (liste)
1. **Web-static non connecté API (micro/text/images)**
   - Impact: UX trompeuse (fonctionne visuellement mais rien n'est sauvegardé).
   - Complexité: **M**
   - Dépendances: appels `fetch` vers `/api/v1` (entries, assets, auth).
   - Risques: incohérences format MediaRecorder selon navigateurs.
2. **Limites et quotas (images / global)**
   - Impact: pas de limite explicite nombre d'images par entry ni quota global user.
   - Complexité: **M**
   - Dépendances: config + validation côté upload/list.
   - Risques: dépassement disque, abus.
3. **Readiness sans check images_dir**
   - Impact: readyz ne vérifie que db + audio_dir; pannes disque images non détectées.
   - Complexité: **S**
   - Dépendances: ajout check écriture `images_dir` dans readyz.
4. **Politique WORM (traçabilité)**
   - Impact: freeze bloque bien modif/suppression; pas d'audit trail immuable des actions.
   - Complexité: **M**
   - Dépendances: définition métier (logs, historique freeze/delete).
   - Risques: conformité, débogage.

## 7) Recommandations (sans patch)
- **Option A**: `POST /entries` multipart unique (`text` + `audio?` + `images[]?`) en une transaction logique.
- **Option B**: `POST /entries` (texte/audio optionnels) puis `POST /entries/{id}/assets` (multipart, audio/images).

**Option B est en place** (création entry avec texte/audio optionnels, sous-ressources `/audio`, `/assets`). Recommandation inchangée.
- L'API actuelle a déjà une ressource `entries` distincte et des endpoints dérivés (`/entries/{id}/audio`, `/freeze`, `/delete`), ce qui favorise une extension orientée sous-ressources.
- Elle limite la complexité du endpoint de création initiale et réduit les risques d'échecs multipart "tout-ou-rien" sur de gros uploads.
- Elle facilite le support futur du chunk upload (audio) sans casser la création d'entry.
- Elle s'aligne avec les besoins ACL/freeze par ressource (entry puis assets attachés).
- Elle simplifie la reprise client (retry upload asset sans recréer l'entry).
- Elle permet d'ajouter types d'assets futurs (image/audio/document) en conservant un contrat stable.

**Short-list env vars à prévoir (max recommandé)**
- `MAX_UPLOAD_AUDIO_MB`
- `MAX_UPLOAD_IMAGE_MB`
- `MAX_IMAGES_PER_ENTRY`
- `MAX_TOTAL_ASSETS_MB_PER_ENTRY`
- `ALLOWED_AUDIO_MIME_TYPES`
- `ALLOWED_IMAGE_MIME_TYPES`
- `ALLOWED_AUDIO_EXTENSIONS`
- `ALLOWED_IMAGE_EXTENSIONS`
- `MAX_TEXT_CHARS`
