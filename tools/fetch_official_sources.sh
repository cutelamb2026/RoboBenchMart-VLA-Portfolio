#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/upstream_sources"
clone_one() {
  local name="$1" url="$2"
  local dest="$ROOT/upstream_sources/$name"
  if [[ -d "$dest/.git" ]]; then
    echo "[SKIP] $name already cloned; do not overwrite it."
  elif [[ -e "$dest" ]]; then
    echo "[ERROR] $dest exists but is not a git checkout; refusing overwrite." >&2
    exit 2
  else
    git clone --recurse-submodules "$url" "$dest"
  fi
  (cd "$dest" && git rev-parse HEAD) > "$ROOT/upstream_sources/${name}_COMMIT.txt"
  echo "$name commit: $(cat "$ROOT/upstream_sources/${name}_COMMIT.txt")"
}
clone_one RoboBenchMart https://github.com/emb-ai/RoboBenchMart.git
clone_one openpi https://github.com/Physical-Intelligence/openpi.git
printf '\n[OK] Official sources are in upstream_sources/. Recovered historical files remain untouched.\n'
