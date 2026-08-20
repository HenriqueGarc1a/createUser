"""Row widget representing a single user in the main list."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, Gtk

from services.user_service import UserRecord


class UserRow(Adw.ActionRow):
    def __init__(
        self,
        record: UserRecord,
        on_reset_password: Callable[[UserRecord], None],
        on_delete: Callable[[UserRecord], None],
    ):
        super().__init__()
        self.record = record

        self.set_title(record.full_name)
        subtitle = record.username
        if record.registration:
            subtitle += f"\nMatrícula: {record.registration}"
        self.set_subtitle(subtitle)
        self.set_subtitle_lines(2)

        reset_button = Gtk.Button(label="Resetar senha", valign=Gtk.Align.CENTER)
        reset_button.add_css_class("flat")
        reset_button.connect("clicked", lambda _b: on_reset_password(record))
        self.add_suffix(reset_button)

        menu_model = Gio.Menu()
        menu_model.append("Excluir usuário", "row.delete")

        menu_button = Gtk.MenuButton(
            icon_name="view-more-symbolic", valign=Gtk.Align.CENTER, menu_model=menu_model
        )
        menu_button.add_css_class("flat")
        self.add_suffix(menu_button)

        action_group = Gio.SimpleActionGroup()
        delete_action = Gio.SimpleAction.new("delete", None)
        delete_action.connect("activate", lambda *_a: on_delete(record))
        action_group.add_action(delete_action)
        self.insert_action_group("row", action_group)
