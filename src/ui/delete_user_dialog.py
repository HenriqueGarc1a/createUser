"""'Excluir usuário' confirmation — requires typing the matrícula, spec
section 26. The delete button only enables once it matches; the helper
re-validates the match server-side regardless (section 21)."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from services.privileged_service import HelperResponse
from services.user_service import UserRecord, delete_user
from ui.messages import friendly_message


class DeleteUserDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window, record: UserRecord, on_deleted: Callable[[], None]):
        super().__init__(transient_for=parent, modal=True, default_width=420)
        self._record = record
        self._on_deleted = on_deleted
        self.set_title("Excluir usuário")

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False))
        self.set_content(toolbar_view)

        clamp = Adw.Clamp(margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        toolbar_view.set_content(clamp)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        clamp.set_child(box)

        heading = Gtk.Label(
            label=f"Excluir {record.full_name}?", css_classes=["title-2"], xalign=0, wrap=True
        )
        box.append(heading)

        subtitle = Gtk.Label(
            label=f"Username: {record.username}", xalign=0, css_classes=["dim-label"]
        )
        box.append(subtitle)

        group = Adw.PreferencesGroup(description="Digite a matrícula para confirmar:")
        box.append(group)
        self._confirm_row = Adw.EntryRow(title="Matrícula")
        self._confirm_row.connect("changed", self._on_field_changed)
        group.add(self._confirm_row)

        self._error_label = Gtk.Label(
            wrap=True, xalign=0, css_classes=["error"], visible=False
        )
        box.append(self._error_label)

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=12, halign=Gtk.Align.END
        )
        box.append(button_box)

        cancel_button = Gtk.Button(label="Cancelar")
        cancel_button.connect("clicked", lambda _b: self.close())
        button_box.append(cancel_button)

        self._delete_button = Gtk.Button(label="Excluir", sensitive=False)
        self._delete_button.add_css_class("destructive-action")
        self._delete_button.connect("clicked", self._on_submit)
        button_box.append(self._delete_button)

    def _on_field_changed(self, _entry: Gtk.Editable) -> None:
        typed = self._confirm_row.get_text().strip()
        matches = bool(self._record.registration) and typed == self._record.registration
        self._delete_button.set_sensitive(matches)
        self._error_label.set_visible(False)

    def _on_submit(self, _button: Gtk.Button) -> None:
        self._delete_button.set_sensitive(False)
        confirm = self._confirm_row.get_text()
        delete_user(self._record.username, confirm, self._on_result)

    def _on_result(self, response: HelperResponse) -> None:
        if response.ok:
            self.close()
            self._on_deleted()
        else:
            self._error_label.set_label(friendly_message(response.code, response.message))
            self._error_label.set_visible(True)
            self._delete_button.set_sensitive(True)
