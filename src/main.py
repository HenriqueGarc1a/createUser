#!/usr/bin/env python3
"""Ubuntu User Manager — unprivileged GUI entrypoint.

Never runs as root and never executes administrative commands directly;
all privileged work is delegated through Polkit to the helper (see
services/privileged_service.py).
"""

from __future__ import annotations

import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio

from ui.main_window import MainWindow


class UserManagerApplication(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.local.usermanager",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        self._window: MainWindow | None = None

    def do_activate(self) -> None:
        if self._window is None:
            self._window = MainWindow(self)
        self._window.present()


def main() -> int:
    app = UserManagerApplication()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
