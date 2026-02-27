# P0-1 — SPEC Freeze/WORM pour Entry + Assets

## Decision

- **Décision produit**: `Frozen = immutable`.
- Quand `entry.is_frozen = true`, **toute mutation** sur l’entry et ses assets est interdite.
- Les opérations de lecture restent autorisées.
- Le freeze est **irréversible** (pas d’unfreeze fonctionnel).

---

## Rules

### 1) Périmètre (routes/actions concernées)

Sont dans le périmètre **toutes les routes mutantes** liées à une entry:

1. Toute modification de l’entry, quel que soit le champ, via `PUT` / `PATCH`.
2. Ajout/remplacement d’asset audio via `POST`.
3. Suppression d’asset audio via `DELETE`.
4. Suppression de l’entry via `DELETE`.
5. Freeze via `POST /entries/{id}/freeze`.
6. Unfreeze (si endpoint exposé) doit être refusé.

### 2) Définition de “mutation”

Est une mutation toute requête qui modifie l’état persistant de l’entry ou de ses assets, notamment:

- `PUT`/`PATCH` entry
- `POST` upload audio
- `DELETE` audio
- `DELETE` entry
- Toute autre action écrivant en base/fichiers sur ce périmètre

### 3) Règle principale (normative)

**GIVEN** une entry existante avec `is_frozen=true`  
**WHEN** une route mutante est appelée sur cette entry ou ses assets  
**THEN** la requête est rejetée avec `409 Conflict`.

### 4) Priorité des statuts (verrouillée)

Pour les routes mutantes:

1. `404 Not Found` si entry/asset n’existe pas (prioritaire).
2. `403 Forbidden` si la ressource existe mais ACL/ownership refuse.
3. `409 Conflict` si la ressource existe, autorisée, et `is_frozen=true`.

### 5) Endpoint freeze

`POST /entries/{id}/freeze`:

- si `is_frozen=false` => passe à `true`, retourne `200` avec body:
  `{"status": "frozen", "id": "<entry_id>", "is_frozen": true}`
- si `is_frozen=true` => idempotent, retourne **le même succès** (`200` + même body).

### 6) Lecture et not found

- Les endpoints `GET` restent autorisés selon ACL existantes.
- Les cas not found restent inchangés (`404`), indépendamment de l’état frozen.

---

## HTTP semantics

### Convention explicite

- `409 Conflict` = état métier incompatible (`is_frozen=true`) pour une mutation.
- `403 Forbidden` = refus ACL/ownership/authz.
- `404 Not Found` = ressource inexistante.

Payload standard pour tout `409` lié au freeze:

```json
{
  "error_code": "ENTRY_FROZEN_IMMUTABLE",
  "detail": "Entry is frozen and cannot be modified"
}
```

---

## Test matrix

| Action | Précondition | Autorisé ? | Code HTTP attendu | Notes |
|---|---|---:|---|---|
| `GET /entries/{id}` | entry existe | Oui | 200 | Lecture inchangée |
| `PATCH /entries/{id}` | entry absente | Non | 404 | Priorité not found |
| `PATCH /entries/{id}` | entry existe, non-owner | Non | 403 | Priorité ACL |
| `PATCH /entries/{id}` | entry existe, owner, frozen=true | Non | 409 | Payload freeze standard |
| `POST /entries/{id}/audio` | entry absente | Non | 404 | Priorité not found |
| `POST /entries/{id}/audio` | entry existe, non-owner | Non | 403 | Priorité ACL |
| `POST /entries/{id}/audio` | entry existe, owner, frozen=true, fichier valide | Non | 409 | Refus même fichier valide |
| `DELETE /entries/{id}/audio` | entry absente | Non | 404 | Priorité not found |
| `DELETE /entries/{id}/audio` | entry existe, non-owner | Non | 403 | Priorité ACL |
| `DELETE /entries/{id}/audio` | entry existe, owner, frozen=true | Non | 409 | Payload freeze standard |
| `DELETE /entries/{id}` | entry absente | Non | 404 | Priorité not found |
| `DELETE /entries/{id}` | entry existe, non-owner | Non | 403 | Priorité ACL |
| `DELETE /entries/{id}` | entry existe, owner, frozen=true | Non | 409 | Payload freeze standard |
| `POST /entries/{id}/freeze` | entry existe, owner, frozen=false | Oui | 200 | Gèle l’entry |
| `POST /entries/{id}/freeze` | entry existe, owner, frozen=true | Oui | 200 | Idempotent |
| `POST /entries/{id}/unfreeze` (si existe) | entry existe | Non | 409 | Unfreeze interdit |

---

## Examples

### Nominal non-frozen

**GIVEN** `entry: 123`, owner, `is_frozen=false`  
**WHEN** client envoie `PATCH /entries/123`  
**THEN** succès (`200/204` selon endpoint).

### Interdit frozen

**GIVEN** `entry: 123`, owner, `is_frozen=true`  
**WHEN** client envoie `DELETE /entries/123`  
**THEN** `409` + payload `ENTRY_FROZEN_IMMUTABLE`.

### Priorité ACL sur frozen

**GIVEN** `entry: 123`, non-owner, `is_frozen=true`  
**WHEN** client envoie `DELETE /entries/123`  
**THEN** `403 Forbidden` (ACL prioritaire), pas `409`.

### Priorité not found

**GIVEN** `entry: not-found`  
**WHEN** client envoie `POST /entries/not-found/audio`  
**THEN** `404 Not Found`.
