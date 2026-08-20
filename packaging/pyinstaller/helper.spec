# PyInstaller spec for the privileged helper. Onefile is fine here: the
# helper is short-lived, has no GTK dependency, and startup latency is
# irrelevant for a single privileged call.

import os

block_cipher = None

REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
HELPER_DIR = os.path.join(REPO_ROOT, "helper")
SRC_DIR = os.path.join(REPO_ROOT, "src")

a = Analysis(
    [os.path.join(HELPER_DIR, "user_manager_helper.py")],
    pathex=[HELPER_DIR, SRC_DIR],
    binaries=[],
    datas=[],
    hiddenimports=["operations", "linux_users", "groups_policy"],
    hookspath=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="user-manager-helper",
    debug=False,
    strip=False,
    upx=False,
    console=True,
)
