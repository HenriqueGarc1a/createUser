#!/bin/sh
# Orchestrates the full .deb build: runs both PyInstaller freezes,
# assembles the staging tree (spec section 37), substitutes the version,
# and calls dpkg-deb. Meant to run inside the Docker build image.
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST_DIR="$REPO_ROOT/dist"
STAGE_DIR="$REPO_ROOT/build/deb-stage"
VERSION="$(cat "$REPO_ROOT/VERSION")"

echo "==> Building version $VERSION"

"$REPO_ROOT/packaging/pyinstaller/build.sh"

rm -rf "$STAGE_DIR"
mkdir -p \
    "$STAGE_DIR/opt/ubuntu-user-manager" \
    "$STAGE_DIR/usr/lib/ubuntu-user-manager/helpers" \
    "$STAGE_DIR/usr/share/polkit-1/actions" \
    "$STAGE_DIR/usr/share/applications" \
    "$STAGE_DIR/DEBIAN"

echo "==> Assembling staging tree at $STAGE_DIR"

cp -r "$REPO_ROOT/packaging/pyinstaller/dist/ubuntu-user-manager/." \
    "$STAGE_DIR/opt/ubuntu-user-manager/"

cp "$REPO_ROOT/packaging/pyinstaller/dist/user-manager-helper" \
    "$STAGE_DIR/usr/lib/ubuntu-user-manager/user-manager-helper"

cp "$REPO_ROOT/helper/entrypoints/create-user" \
   "$REPO_ROOT/helper/entrypoints/reset-password" \
   "$REPO_ROOT/helper/entrypoints/delete-user" \
    "$STAGE_DIR/usr/lib/ubuntu-user-manager/helpers/"

cp "$REPO_ROOT/polkit/com.local.usermanager.policy" \
    "$STAGE_DIR/usr/share/polkit-1/actions/com.local.usermanager.policy"

cp "$REPO_ROOT/desktop/ubuntu-user-manager.desktop" \
    "$STAGE_DIR/usr/share/applications/ubuntu-user-manager.desktop"

for script in postinst prerm postrm; do
    cp "$REPO_ROOT/packaging/debian/$script" "$STAGE_DIR/DEBIAN/$script"
    chmod 0755 "$STAGE_DIR/DEBIAN/$script"
done

sed "s/__VERSION__/$VERSION/" "$REPO_ROOT/packaging/debian/control" > "$STAGE_DIR/DEBIAN/control"

chmod 0755 "$STAGE_DIR/usr/lib/ubuntu-user-manager/user-manager-helper"
chmod 0755 "$STAGE_DIR/usr/lib/ubuntu-user-manager/helpers/"*
chmod 0644 "$STAGE_DIR/usr/share/polkit-1/actions/com.local.usermanager.policy"
chmod 0644 "$STAGE_DIR/usr/share/applications/ubuntu-user-manager.desktop"

mkdir -p "$DIST_DIR"
OUTPUT="$DIST_DIR/ubuntu-user-manager_${VERSION}_amd64.deb"

echo "==> Building $OUTPUT"

if dpkg-deb --help 2>&1 | grep -q -- --root-owner-group; then
    dpkg-deb --root-owner-group --build "$STAGE_DIR" "$OUTPUT"
else
    echo "==> dpkg-deb --root-owner-group unsupported, falling back to fakeroot"
    fakeroot dpkg-deb --build "$STAGE_DIR" "$OUTPUT"
fi

echo "==> Built $OUTPUT"
