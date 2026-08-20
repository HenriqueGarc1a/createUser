#!/bin/sh
# Development convenience installer — NOT the official distribution
# method. The official method is always the .deb built by `make release`
# (see README). This script requires sudo and installs the already-built
# .deb from dist/.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DEB_FILE="$(ls "$REPO_ROOT"/dist/*.deb 2>/dev/null | head -1)"

if [ -z "${DEB_FILE:-}" ]; then
    echo "Nenhum .deb encontrado em dist/. Rode 'make release' primeiro." >&2
    exit 1
fi

echo "==> Instalando $DEB_FILE"
sudo apt install "$DEB_FILE"
