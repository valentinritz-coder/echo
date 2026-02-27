# Echo MVP — Audit fonctionnalités "Souvenir multimédia"

## 0) Contexte et périmètre
- **Scope analysé**: backend FastAPI (`services/api`) + front web statique (`apps/web-static`) + front Streamlit (`apps/web`) pour l’état réel des fonctionnalités audio/texte/images autour des entries.
- **Hors scope**: implémentation d’un nouveau design, correctifs, migrations additionnelles, optimisation UX, infra prod.
- **Hypothèses**:
  - Les formats audio produits navigateur (souvent `audio/webm`/`audio/ogg` selon UA) sont potentiellement acceptés côté API si MIME + signature/extension sont cohérents.
  - Le front statique est une UI MVP de démonstration (pas encore branchée API) malgré des composants présents.
  - Le front Streamlit est actuellement le client réellement connecté à l’API pour créer/lire des entries audio.

## 1) Cartographie rapide du repo

### Backend (services/api)
- **Points d’entrée (routes)**
  - `GET /api/v1/version`, `GET /api/v1/questions/today`, `POST /api/v1/entries`, `GET /api/v1/entries`, `GET /api/v1/entries/{entry_id}`, `POST /api/v1/entries/{entry_id}/freeze`, `GET /api/v1/entries/{entry_id}/audio`, `DELETE /api/v1/entries/{entry_id}` dans `app/main.py`.
  - `POST /api/v1/auth/login`, `POST /api/v1/auth/refresh` dans `app/routes/auth.py`.
  - `GET /api/v1/health`, `GET /api/v1/readyz` dans `app/routes/system.py`.
- **Modèles DB pertinents (entries/users/assets)**
  - `users`, `questions`, `entries` existent.
  - `entries` contient: `id`, `user_id`, `question_id`, `audio_path`, `audio_mime`, `audio_size`, `audio_sha256`, `audio_duration_ms`, `is_frozen`, `created_at`.
  - **Aucune table assets/images** et **aucun champ texte entry**.
- **Stockage fichiers (audio/images)**
  - Audio stocké sur disque sous `DATA_DIR/audio/<uuid>.<ext>`.
  - Check de readiness sur `audio_dir` en écriture.
  - Aucun stockage image implémenté.
- **Sécurité (JWT, ACL, freeze/WORM)**
  - JWT access/refresh via `/auth/login` et `/auth/refresh`.
  - ACL propriétaire sur `GET entry`, `GET audio`, `DELETE entry`, `POST freeze`.
  - Freeze (`is_frozen`) bloque la suppression (409), proche logique WORM sur delete entry.

### Frontend (apps/web-static)
- **Pages/JS existants**
  - `index.html` inclut composer avec `textarea`, bouton micro, input images multiple, submit.
  - `app.js` gère autosize texte, preview images locale, enregistrement micro `MediaRecorder` + preview audio.
- **Appels API existants**
  - Aucun `fetch()`/appel `/api/v1` dans `apps/web-static/app.js`.
- **UI existante liée aux entries**
  - Sidebar timeline alimentée par données fake (`memories` hardcodées).
  - Pas de chargement des entries API ni rendu réel d’une entry serveur.

## 2) État des fonctionnalités (tableau)

| Feature | Status (OK/Partiel/Absent) | Preuves (fichiers + lignes/fonctions) | Gaps | Notes/risques |
|---|---|---|---|---|
| Upload audio (déjà) + endpoints de download | **OK** | `POST /entries` (multipart `question_id` + `audio_file`) et stockage disque; `GET /entries/{id}/audio` renvoie `FileResponse`. | Pas d’endpoint audio public/signé; download seulement via auth user propriétaire. | Solide pour audio seul; bien cadré ACL + MIME. |
| Record micro depuis web (`getUserMedia`/`MediaRecorder`) | **Partiel** | `apps/web-static/app.js` implémente `getUserMedia`, `MediaRecorder`, création `Blob`, preview `<audio>`. | Pas d’upload API du blob enregistré; pas d’assemblage multipart; pas de chunk upload. | UX micro existe mais non persistée backend. |
| Texte entry (création + retrieval) | **Absent** | `Entry` model + `EntryOut` ne contiennent aucun champ texte; `POST /entries` n’accepte que `question_id` + `audio_file`. | DB, schéma API, endpoints et UI backend manquants pour texte persistant. | Le `textarea` web-static est purement UI locale. |
| Upload images (1..n) + metadata + download | **Absent** | Input file images + preview locale dans web-static; aucun endpoint image côté API, aucune table assets/images. | Tout le flux backend manque (upload, metadata, listing, download, ACL). | Risque d’illusion fonctionnelle côté UI. |
| Listing entries (pagination/tri) et si assets apparaissent ou non | **Partiel** | `GET /entries` avec `limit/offset/sort` et réponse wrapper (`items,next_offset,limit,offset`). | Les assets (images/audio URL) et texte ne figurent pas dans `EntryOut`; pas de projection multimédia riche. | Listing API est audio-metadata-centric. |
| ACL (cross-user) sur entry + audio + images | **Partiel** | ACL propriétaire présente sur entry/audio/delete/freeze; test ACL cross-user existe. | Pas d’assets images, donc ACL images inexistante. | Base ACL correcte sur l’existant audio. |
| Freeze/WORM impact (modif/suppression) | **Partiel** | `POST /entries/{id}/freeze` + `DELETE` interdit si `is_frozen` (409); tests freeze existent. | Pas de notion WORM sur assets annexes (images) ni sur update champs (puisqu’absents). | Freeze couvre suppression entry/audio par cascade logique actuelle. |
| Validations MIME/signature (audio, images) | **Partiel** | Audio: whitelist MIME + signature binaire + extension cohérente + limite taille dans `storage.py`. | Aucune validation image (MIME/signature/extension) car feature absente. | Contrôles audio assez stricts pour MVP. |
| Limites de taille / env vars | **Partiel** | `max_upload_size_mb` (default 25) -> `max_upload_bytes`; appliqué au stream upload audio. | Pas de limites séparées audio/image, ni limite nombre images, ni quotas par entry/user. | Dimensionnement image non traité. |

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
  - `POST /api/v1/entries` (Bearer, multipart):
    - `question_id` (form int)
    - `audio_file` (file)
    - réponse: `EntryOut{id,user_id,question_id,audio_mime,audio_size,is_frozen,created_at}`
  - `GET /api/v1/entries` (Bearer, query): `limit`, `offset`, `sort in [created_at_desc, created_at_asc, id_asc, id_desc]` → `{items,next_offset,limit,offset}`
  - `GET /api/v1/entries/{entry_id}` (Bearer) → `EntryOut`
  - `GET /api/v1/entries/{entry_id}/audio` (Bearer) → binaire audio (`FileResponse`)
  - `POST /api/v1/entries/{entry_id}/freeze` (Bearer) → `{status:"frozen",id,is_frozen:true}`
  - `DELETE /api/v1/entries/{entry_id}` (Bearer) → `{status:"deleted",id}` ou `409 frozen`
- **Endpoints assets/images**: non détectés.

## 4) DB / migrations
- **Schéma actuel pertinent**
  - `questions` créée en 0001.
  - `entries` créée en 0001 avec audio de base (`audio_path`, `audio_mime`, `audio_size`, `created_at`).
  - `users` ajoutée en 0002 + FK `entries.user_id -> users.id`.
  - `entries` enrichie en 0004 (`audio_sha256`, `audio_duration_ms`) puis 0005 (`is_frozen`).
- **Index existants**
  - `ix_entries_user_id` (0001)
  - `ix_entries_user_id_created_at_id` (0003) pour pagination/tri
  - `ix_users_email`, `ix_questions_id`
- **Manques constatés pour texte/images**
  - Pas de colonne texte (`content_text`, etc.) dans `entries`.
  - Pas de table `assets`/`entry_images`/`entry_files`.
  - Pas de metadata image (mime, size, sha256, width/height).
  - Pas d’index ciblant des assets puisque entité absente.

## 5) Frontend: capacités actuelles
- **MediaRecorder / input file / textarea**
  - `apps/web-static`: oui pour les trois (textarea, micro, images input multiple) mais uniquement côté UI locale.
  - `apps/web` (Streamlit): pas de MediaRecorder navigateur; upload fichier audio manuel via `file_uploader`.
- **Flux exact actuel pour créer une entry et uploader l’audio**
  1. Login via `/auth/login`.
  2. Récupération question via `/questions/today`.
  3. Upload multipart vers `/entries` avec `question_id` + `audio_file`.
  4. Listing `/entries`, lecture audio via `/entries/{id}/audio`, téléchargement depuis bytes récupérés.
- **Ce qui manque pour texte/images/record micro**
  - `web-static`: pas de submit branché API (pas de `fetch`), donc ni texte ni images ni audio micro persistés.
  - `web`: pas de champ texte entry ni upload images.
  - `backend`: aucun support texte/images.

## 6) Gaps prioritaires (liste)
1. **Absence de modèle de données multimédia (texte + assets images)**
   - Impact: impossible de stocker un souvenir complet multimédia.
   - Complexité: **L**
   - Dépendances: migration DB + schémas + routes.
   - Risques: migration rétrocompatible, volumétrie stockage.
2. **API de création/gestion assets images absente**
   - Impact: photo(s) non sauvegardables/non téléchargeables.
   - Complexité: **L**
   - Dépendances: modèle DB assets + stockage disque + ACL.
   - Risques: sécurité upload (MIME spoofing), quota disque.
3. **Pas de persistance du texte entry**
   - Impact: perte de la valeur narrative principale pour une partie des usages.
   - Complexité: **M**
   - Dépendances: colonne DB + validation API + rendu UI.
   - Risques: sanitization/affichage, taille max texte.
4. **Web-static non connecté API (micro/text/images)**
   - Impact: UX trompeuse (fonctionne visuellement mais rien n’est sauvegardé).
   - Complexité: **M**
   - Dépendances: endpoints disponibles d’abord.
   - Risques: incohérences format MediaRecorder selon navigateurs.
5. **Projection API trop limitée pour lecture “entry multimédia”**
   - Impact: impossible d’afficher une entry avec texte + images + audio en un flux.
   - Complexité: **M**
   - Dépendances: enrichissement schémas de sortie + endpoints assets.
   - Risques: N+1 et payloads lourds si non paginés pour assets.
6. **Contrôles upload incomplets hors audio**
   - Impact: surface d’attaque/erreurs élevée pour futures images.
   - Complexité: **M**
   - Dépendances: implémentation image backend.
   - Risques: fichiers malicieux, dépassement quota.
7. **Politique WORM partielle**
   - Impact: freeze ne couvre aujourd’hui que le périmètre entry audio existant.
   - Complexité: **M**
   - Dépendances: définition métier freeze sur texte/assets.
   - Risques: suppression/modification partielle incohérente.

## 7) Recommandations (sans patch)
- **Option A**: `POST /entries` multipart unique (`text` + `audio?` + `images[]?`) en une transaction logique.
- **Option B**: `POST /entries` (JSON texte + métadonnées) puis `POST /entries/{id}/assets` (multipart, audio/images).

**Option recommandée: B (plus alignée avec l’existant).**
- L’API actuelle a déjà une ressource `entries` distincte et des endpoints dérivés (`/entries/{id}/audio`, `/freeze`, `/delete`), ce qui favorise une extension orientée sous-ressources.
- Elle limite la complexité du endpoint de création initiale et réduit les risques d’échecs multipart “tout-ou-rien” sur de gros uploads.
- Elle facilite le support futur du chunk upload (audio) sans casser la création d’entry.
- Elle s’aligne avec les besoins ACL/freeze par ressource (entry puis assets attachés).
- Elle simplifie la reprise client (retry upload asset sans recréer l’entry).
- Elle permet d’ajouter types d’assets futurs (image/audio/document) en conservant un contrat stable.

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
