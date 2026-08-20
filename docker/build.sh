#!/bin/sh
# Docker ENTRYPOINT: runs the full build inside the container and copies
# the resulting .deb out to the bind-mounted /dist volume.
set -eu

cd /build

./packaging/build-deb.sh

mkdir -p /dist
cp dist/*.deb /dist/

echo "==> Copied to /dist:"
ls -la /dist/*.deb
