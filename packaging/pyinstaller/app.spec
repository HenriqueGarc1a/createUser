# PyInstaller spec for the GUI application.
#
# Strategy: freeze only the Python interpreter + application code
# (including the compiled `gi._gi` extension). GTK4, Libadwaita and their
# typelibs are NOT bundled — they are expected to come from the target
# system via the .deb's `Depends:` (see packaging/debian/control). This
# sidesteps PyInstaller's well-known fragility around discovering
# non-Python data files (typelibs, shared libs) for PyGObject apps: its
# import-graph analysis only follows Python imports, so GI's typelibs are
# invisible to it no matter what's added to hiddenimports. Mixing a
# frozen GTK with the system's GTK also risks ABI/theme mismatches, so we
# avoid it entirely.

import os

block_cipher = None

REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")

a = Analysis(
    [os.path.join(SRC_DIR, "main.py")],
    pathex=[SRC_DIR],
    binaries=[],
    datas=[],
    hiddenimports=[
        "gi",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Gio",
        "gi.repository.Gdk",
        "gi.repository.Gtk",
        "gi.repository.Adw",
    ],
    hookspath=[os.path.join(SPECPATH, "hooks")],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)

# Defensive filter: even with no explicit datas/binaries above, some
# PyInstaller/hook combinations try to auto-collect shared libraries
# discovered via ctypes/dlopen introspection. Strip anything that looks
# like a GTK/GLib/Adwaita/GObject-introspection runtime lib or typelib so
# the frozen bundle never ships a copy that could shadow or conflict with
# the system's own at runtime.
_EXCLUDED_BINARY_MARKERS = (
    "libgtk-4",
    "libadwaita",
    "libgobject",
    "libglib",
    "libgio",
    "girepository",
)
a.binaries = [
    entry
    for entry in a.binaries
    if not any(marker in entry[0].lower() for marker in _EXCLUDED_BINARY_MARKERS)
]
a.datas = [entry for entry in a.datas if not entry[0].lower().endswith(".typelib")]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ubuntu-user-manager",
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name="ubuntu-user-manager",
)
