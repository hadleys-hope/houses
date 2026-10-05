#!/usr/bin/env bash
# Compile every program in programs/ to build/<name>.hbc.
#   HOPEC=path/to/compiler/bin ./build.sh
set -euo pipefail

HOPEC="${HOPEC:-hopec}"
SRC="$(dirname "$0")/programs"
OUT="$(dirname "$0")/build"

compile_all() {
    mkdir -p "$OUT"
    local ok=0
    for f in "$SRC"/*.hope; do
        local name
        name="$(basename "$f" .hope)"
        "$HOPEC" --compile "$f" "$OUT/$name.hbc" > /dev/null
        echo "  compiled $name -> build/$name.hbc"
        ok=$((ok + 1))
    done
    echo "== $ok programs compiled"
}

compile_all
