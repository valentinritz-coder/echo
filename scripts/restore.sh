#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[restore] %s\n' "$*"
}

die() {
  printf '[restore] ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<'USAGE'
Usage: scripts/restore.sh <backup_tar_or_tar_gz> [--dest-dir <path>]

Options:
  --dest-dir <path>  Base restore directory (default: <repo_root>/data_restore)
  -h, --help         Show this help message
USAGE
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" ]]; then
  repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
fi
dest_root="$repo_root/data_restore"
backup_file=""

if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest-dir)
      [[ $# -ge 2 ]] || die "Missing value for --dest-dir"
      dest_root="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -* )
      die "Unknown option: $1"
      ;;
    *)
      if [[ -n "$backup_file" ]]; then
        die "Only one backup file may be provided"
      fi
      backup_file="$1"
      shift
      ;;
  esac
done

[[ -n "$backup_file" ]] || die "Backup archive is required"
[[ -f "$backup_file" ]] || die "Backup archive not found: $backup_file"

archive_name="$(basename "$backup_file")"
archive_base="$archive_name"
archive_base="${archive_base%.tar.gz}"
archive_base="${archive_base%.tgz}"
archive_base="${archive_base%.tar}"
target_dir="$dest_root/$archive_base"

mkdir -p "$dest_root"

if [[ -e "$target_dir" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Target exists ($target_dir). Overwrite? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      die "Restore cancelled by user"
    fi
    rm -rf "$target_dir"
  else
    die "Target already exists in non-interactive mode: $target_dir"
  fi
fi

mkdir -p "$target_dir"

tar -tf "$backup_file" | awk '
  /^\// {bad=1}
  /(^|\/)\.\.(\/|$)/ {bad=1}
  END {exit bad}
' || die "Archive contains unsafe paths (absolute or ..)"

log "Extracting archive into: $target_dir"
tar --no-same-owner --no-same-permissions -xf "$backup_file" -C "$target_dir"

restored_db_snapshot="$target_dir/db/echo.db"
restored_audio_dir="$target_dir/audio"
[[ -f "$restored_db_snapshot" ]] || die "Missing DB snapshot in archive (expected db/echo.db)"
[[ -d "$restored_audio_dir" ]] || die "Missing audio directory in archive (expected audio/)"

cp "$restored_db_snapshot" "$target_dir/echo.db"

if [[ -f "$target_dir/manifest.json" ]]; then
  log "Manifest summary:"
  if command -v python3 >/dev/null 2>&1; then
    python3 - <<'PY' "$target_dir/manifest.json"
import json
import pathlib
import sys

manifest = pathlib.Path(sys.argv[1])
try:
    data = json.loads(manifest.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"  - Unable to parse manifest.json: {exc}")
    sys.exit(0)

print(f"  - created_at_utc: {data.get('created_at_utc', 'n/a')}")
print(f"  - db_path: {data.get('db_path', 'n/a')}")
print(f"  - audio_dir: {data.get('audio_dir', 'n/a')}")
PY
  else
    sed 's/^/  /' "$target_dir/manifest.json"
  fi
fi

log "Restore complete"
log "DB restored at: $target_dir/echo.db"
log "Audio restored at: $target_dir/audio"
log "Run app against this restore with:"
log "  DATA_DIR='$target_dir' docker compose up"
