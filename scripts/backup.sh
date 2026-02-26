#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[backup] %s\n' "$*"
}

die() {
  printf '[backup] ERROR: %s\n' "$*" >&2
  exit 1
}

json_escape() {
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

usage() {
  cat <<'USAGE'
Usage: scripts/backup.sh [options]

Options:
  --data-dir <path>   Data directory (default: $DATA_DIR or <repo_root>/data)
  --out-dir <path>    Backup output directory (default: <repo_root>/backups)
  --db <path>         SQLite DB path (default: <data-dir>/echo.db)
  --audio-dir <path>  Audio directory path (default: <data-dir>/audio)
  --no-compress       Produce a .tar bundle instead of .tar.gz
  -h, --help          Show this help message
USAGE
}

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -z "$repo_root" ]]; then
  repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
fi
data_dir="${DATA_DIR:-$repo_root/data}"
out_dir="$repo_root/backups"
db_path=""
audio_dir=""
compress=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --data-dir)
      [[ $# -ge 2 ]] || die "Missing value for --data-dir"
      data_dir="$2"
      shift 2
      ;;
    --out-dir)
      [[ $# -ge 2 ]] || die "Missing value for --out-dir"
      out_dir="$2"
      shift 2
      ;;
    --db)
      [[ $# -ge 2 ]] || die "Missing value for --db"
      db_path="$2"
      shift 2
      ;;
    --audio-dir)
      [[ $# -ge 2 ]] || die "Missing value for --audio-dir"
      audio_dir="$2"
      shift 2
      ;;
    --no-compress)
      compress=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

if [[ -z "$db_path" ]]; then
  db_path="$data_dir/echo.db"
fi
if [[ -z "$audio_dir" ]]; then
  audio_dir="$data_dir/audio"
fi

[[ -f "$db_path" ]] || die "Database file not found: $db_path"
[[ -d "$audio_dir" ]] || die "Audio directory not found: $audio_dir"
mkdir -p "$out_dir"

timestamp="$(date -u +%Y%m%d_%H%M%SZ)"
ext="tar.gz"
if [[ "$compress" -eq 0 ]]; then
  ext="tar"
fi
bundle_path="$out_dir/echo_backup_${timestamp}.${ext}"

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

mkdir -p "$tmp_dir/db" "$tmp_dir/audio"

if command -v sqlite3 >/dev/null 2>&1; then
  log "Creating SQLite snapshot with sqlite3 .backup"
  sqlite3 "$db_path" ".backup '$tmp_dir/db/echo.db'"
else
  log "sqlite3 not found; falling back to file copy"
  cp "$db_path" "$tmp_dir/db/echo.db"
fi

log "Copying audio directory"
cp -a "$audio_dir/." "$tmp_dir/audio/"

created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
sqlite_version="unavailable"
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite_version="$(sqlite3 --version 2>/dev/null | awk '{print $1}')"
fi
tar_version="$(tar --version 2>/dev/null | head -n 1 || echo unavailable)"
bash_version="${BASH_VERSION:-unavailable}"

cat > "$tmp_dir/manifest.json" <<MANIFEST
{
  "created_at_utc": "$(json_escape "$created_at")",
  "db_path": "$(json_escape "$db_path")",
  "audio_dir": "$(json_escape "$audio_dir")",
  "tool_versions": {
    "bash": "$(json_escape "$bash_version")",
    "sqlite3": "$(json_escape "$sqlite_version")",
    "tar": "$(json_escape "$tar_version")"
  }
}
MANIFEST

log "Writing bundle: $bundle_path"
if [[ "$compress" -eq 1 ]]; then
  tar -C "$tmp_dir" -czf "$bundle_path" manifest.json db audio
else
  tar -C "$tmp_dir" -cf "$bundle_path" manifest.json db audio
fi

log "Backup complete"
log "Bundle available at: $bundle_path"
