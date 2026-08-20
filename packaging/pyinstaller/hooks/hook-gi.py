# Custom hook for `gi`, placed in hookspath so it takes precedence over
# any community hook (pyinstaller-hooks-contrib) that might try to
# auto-collect GTK typelibs/shared libraries as datas/binaries. We only
# want the compiled `gi._gi` extension module and pure-Python glue code
# frozen; GTK4/Libadwaita/GLib themselves must come from the target
# system (see app.spec's top-level comment for the rationale).

hiddenimports = [
    "gi._gi",
    "gi._gi_cairo",
    "gi.overrides",
    "gi.repository",
]

# Deliberately empty: no typelibs, no shared libraries.
datas = []
binaries = []
