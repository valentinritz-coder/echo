# P0-1 — SPEC Freeze/WORM pour Entry + Assets

## Decision

- **Décision produit**: `Frozen = immutable`.
- Quand `entry.is_frozen = true`, **toute mutation** sur l’entry et ses assets est interdite.
- Les opérations de lecture restent autorisées.
- Le freeze est considéré **irréversible**: pas d’endpoint d’unfreeze (ou unfreeze explicitement interdit si endpoint historique existe).

---

## Rules

### 1) Périmètre (routes/actions concernées)

Sont dans le périmètre **toutes les routes mutantes** liées à une entry:

1. Mutation du contenu de l’entry (texte, métadonnées éditables, etc.) via `PUT` / `PATCH`.
2. Ajout d’asset (upload image/audio/etc.) via `POST` (multipart ou équivalent).
3. Suppression d’un asset via `DELETE`.
4. Suppression de l’entry via `DELETE`.
5. Action de freeze (si endpoint dédié) autorisée uniquement pour passer de `is_frozen=false` à `true`.
6. Action d’unfreeze (si endpoint existe) interdite.

### 2) Définition de “mutation”

Est une mutation toute requête qui modifie l’état persistant de l’entry ou de ses assets, notamment:

- `PUT`/`PATCH` entry
- `POST` upload asset
- `DELETE` asset
- `DELETE` entry
- Toute autre action écrivant en base/fichiers sur ce périmètre

### 3) Règle principale (normative)

**GIVEN** une entry existante avec `is_frozen=true`  
**WHEN** une route mutante est appelée sur cette entry ou ses assets  
**THEN** la requête est rejetée avec `409 Conflict`.

### 4) Lecture et erreurs hors freeze

- Les endpoints de lecture (`GET`) restent inchangés et autorisés selon ACL existantes.
- Les cas “resource not found” ou identifiants invalides restent inchangés:
  - `404 Not Found` si entry/asset n’existe pas.
  - Ce comportement est indépendant de l’état `is_frozen`.

### 5) Cas explicitement attendus

- Upload asset: si entry frozen, échec `409` même si fichier valide.
- Suppression asset: si entry frozen, échec `409`.
- Update texte/entry: si entry frozen, échec `409`.
- Suppression entry: si entry frozen, échec `409` (aligné existant).

---

## HTTP semantics

### Convention explicite

- `409 Conflict` = l’opération est refusée car **l’état courant de la ressource** est incompatible avec l’action demandée (ici: `is_frozen=true`).
- `403 Forbidden` = refus lié aux **droits/ACL/authz** (acteur non autorisé), pas à l’état métier frozen.

### Application de la convention

Pour toute mutation ciblant une entry frozen (ou ses assets), renvoyer `409`, y compris:

- update entry
- upload asset
- delete asset
- delete entry
- unfreeze (si endpoint exposé)

`403` reste réservé aux refus d’autorisation, indépendamment de freeze.

---

## Test matrix

| Action | Précondition | Autorisé ? | Code HTTP attendu | Notes |
|---|---|---:|---|---|
| `GET /entries/{id}` | entry existe, frozen=false | Oui | 200 | Lecture inchangée |
| `GET /entries/{id}` | entry existe, frozen=true | Oui | 200 | Lecture inchangée |
| `PATCH/PUT /entries/{id}` | entry existe, frozen=false | Oui | 200/204 | Selon implémentation actuelle |
| `PATCH/PUT /entries/{id}` | entry existe, frozen=true | Non | 409 | Frozen => immutable |
| `POST /entries/{id}/assets` | entry existe, frozen=false, fichier valide | Oui | 201/200 | Selon implémentation actuelle |
| `POST /entries/{id}/assets` | entry existe, frozen=true, fichier valide | Non | 409 | Validation fichier sans impact sur la décision |
| `DELETE /entries/{id}/assets/{asset_id}` | entry existe, asset existe, frozen=false | Oui | 204/200 | Selon implémentation actuelle |
| `DELETE /entries/{id}/assets/{asset_id}` | entry existe, asset existe, frozen=true | Non | 409 | Frozen => immutable |
| `DELETE /entries/{id}` | entry existe, frozen=false | Oui | 204/200 | Selon implémentation actuelle |
| `DELETE /entries/{id}` | entry existe, frozen=true | Non | 409 | Alignement comportement existant |
| `POST /entries/{id}/freeze` (si existe) | entry existe, frozen=false | Oui | 200/204 | Transition autorisée vers frozen=true |
| `POST /entries/{id}/freeze` (si existe) | entry existe, frozen=true | Non (idempotence ou conflit selon API) | 200/204 ou 409 | À figer selon contrat actuel |
| `POST /entries/{id}/unfreeze` (si existe) | entry existe, frozen=true | Non | 409 | Unfreeze interdit |
| Toute mutation sur id inexistant | entry absente | Non | 404 | Priorité au not found inchangée |

---

## Examples

### Exemple nominal (non frozen)

**GIVEN** `entry: 123`, `is_frozen=false`  
**WHEN** client envoie `PATCH /entries/123` pour modifier le texte  
**THEN** modification acceptée (`200` ou `204` selon contrat existant).

### Exemple interdit: update texte

**GIVEN** `entry: 123`, `is_frozen=true`  
**WHEN** client envoie `PATCH /entries/123`  
**THEN** réponse `409 Conflict`, aucune modification persistée.

### Exemple interdit: upload asset valide

**GIVEN** `entry: 123`, `is_frozen=true`, fichier audio valide  
**WHEN** client envoie `POST /entries/123/assets`  
**THEN** réponse `409 Conflict`, aucun asset créé.

### Exemple interdit: delete asset

**GIVEN** `entry: 123`, `is_frozen=true`, `asset: a1` existant  
**WHEN** client envoie `DELETE /entries/123/assets/a1`  
**THEN** réponse `409 Conflict`, asset conservé.

### Exemple interdit: delete entry

**GIVEN** `entry: 123`, `is_frozen=true`  
**WHEN** client envoie `DELETE /entries/123`  
**THEN** réponse `409 Conflict`, entry conservée.

### Exemple ACL (différence 403 vs 409)

**GIVEN** `entry: 123`, `is_frozen=false`, utilisateur sans droit d’édition  
**WHEN** client envoie `PATCH /entries/123`  
**THEN** réponse `403 Forbidden` (motif ACL, pas freeze).

---

## Notes d’implémentation (non contraignantes, pour testabilité)

- Centraliser la décision “mutation autorisée ?” dans un garde/validator unique (service ou dépendance FastAPI) pour éviter les divergences entre endpoints.
- Appliquer ce garde à toutes les routes mutantes entry + assets.
- Conserver un message d’erreur stable (ex: `ENTRY_FROZEN_IMMUTABLE`) pour assertions de tests robustes.
- Couvrir tests API par matrice: non frozen (success), frozen (409), unauthorized (403), not found (404).

---

## Dépendances

Aucune dépendance technique pour cette spec (P0-1 spec only).
