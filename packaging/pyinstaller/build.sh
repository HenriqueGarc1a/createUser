#!/bin/sh
# Runs both PyInstaller builds (GUI app + privileged helper). Meant to
# run inside the Docker build image (see Dockerfile) so the frozen
# gi._gi extension's ABI matches the target system's Python/glib.
set -eu

cd "$(dirname "$0")"

pyinstaller --clean --noconfirm app.spec
pyinstaller --clean --noconfirm helper.spec
