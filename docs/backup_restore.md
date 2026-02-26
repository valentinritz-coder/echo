# Backup & restore (SQLite + audio)

Ce projet fournit deux scripts Bash pour sauvegarder et restaurer les données persistées (`echo.db` + dossier `audio/`) de façon sûre.

- Backup: `scripts/backup.sh`
- Restore: `scripts/restore.sh`

## Recommandations

- **Idéalement**, stoppez les conteneurs pendant un backup (`docker compose down`) pour éviter toute activité concurrente.
- Si ce n'est pas possible, le script utilise `sqlite3 .backup` quand `sqlite3` est disponible, ce qui produit un snapshot SQLite cohérent.

## Créer un backup

Commande par défaut (sortie dans `./backups`):

```bash
scripts/backup.sh
```

Exemple de fichier généré:

```text
backups/echo_backup_YYYYmmdd_HHMMSSZ.tar.gz
```

Options utiles:

```bash
scripts/backup.sh --data-dir ./data
scripts/backup.sh --out-dir ./backups
scripts/backup.sh --db ./data/echo.db --audio-dir ./data/audio
scripts/backup.sh --no-compress
```

Contenu de l'archive:

- `manifest.json` (timestamp, chemins source, versions outils)
- `db/echo.db` (snapshot)
- `audio/` (copie complète)

## Restaurer un backup

Usage:

```bash
scripts/restore.sh <backup_tar_or_tar_gz> [--dest-dir <path>]
```

Exemples:

```bash
scripts/restore.sh backups/echo_backup_20260101_120000Z.tar.gz
scripts/restore.sh backups/echo_backup_20260101_120000Z.tar.gz --dest-dir ./data_restore
```

Comportement sécurité:

- La restauration se fait **toujours** dans un sous-dossier de `data_restore/` (ou du `--dest-dir` fourni).
- Le script n'écrase pas silencieusement:
  - En TTY: confirmation demandée avant overwrite.
  - Hors TTY (CI/script): échec explicite si le dossier cible existe.

Après extraction, le script affiche:

- chemin de la DB restaurée
- chemin du dossier audio restauré
- commande à utiliser pour lancer l'app avec `DATA_DIR` pointant vers le restore

## Procédure de test manuelle (recommandée)

1. Créer un backup:

```bash
scripts/backup.sh
```

Attendu: un fichier `backups/echo_backup_*.tar.gz` est créé.

2. Restaurer ce backup:

```bash
scripts/restore.sh backups/echo_backup_*.tar.gz
```

Attendu: un dossier `data_restore/<nom_archive>/` est créé avec:

- `echo.db`
- `audio/`
- `manifest.json`

3. Lancer l'API sur les données restaurées.

En local (depuis `services/api`):

```bash
DATA_DIR="$(pwd)/../../data_restore/<nom_archive>" uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Ou via Docker Compose:

```bash
DATA_DIR="$(pwd)/data_restore/<nom_archive>" docker compose up --build
```

4. Vérifier l'état et les médias:

```bash
curl -i http://localhost:8000/api/v1/readyz
```

Attendu: statut `200`.

Puis vérifier qu'au moins un fichier audio existe (si votre backup contenait des audios):

```bash
find data_restore/<nom_archive>/audio -type f | head -n 5
```

Attendu: au moins un chemin listé.
