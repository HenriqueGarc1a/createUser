"""'+ Criar usuário' modal — name + registration in, generated username
previewed live, password never entered manually (spec section 6)."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from services.privileged_service import HelperResponse
from services.user_service import create_user, preview_username, validate_create_user_fields
from ui.messages import friendly_message


class CreateUserDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window, on_created: Callable[[], None]):
        super().__init__(transient_for=parent, modal=True, default_width=420)
        self._on_created = on_created
        self.set_title("Criar usuário")

        toolbar_view = Adw.ToolbarView()
        toolbar_view.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False))
        self.set_content(toolbar_view)

        clamp = Adw.Clamp(margin_top=24, margin_bottom=24, margin_start=24, margin_end=24)
        toolbar_view.set_content(clamp)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        clamp.set_child(box)

        group = Adw.PreferencesGroup()
        box.append(group)

        self._name_row = Adw.EntryRow(title="Nome completo")
        self._name_row.connect("changed", self._on_field_changed)
        group.add(self._name_row)

        self._registration_row = Adw.EntryRow(title="Matrícula")
        self._registration_row.connect("changed", self._on_field_changed)
        group.add(self._registration_row)

        preview_group = Adw.PreferencesGroup(
            title="Username", description="Gerado automaticamente."
        )
        box.append(preview_group)
        self._username_preview = Adw.ActionRow(title="—")
        preview_group.add(self._username_preview)

        info_group = Adw.PreferencesGroup()
        box.append(info_group)
        info_group.add(
            Adw.ActionRow(
                title="Senha temporária",
                subtitle="A matrícula será utilizada como senha inicial.",
            )
        )

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

        self._submit_button = Gtk.Button(label="Criar usuário", sensitive=False)
        self._submit_button.add_css_class("suggested-action")
        self._submit_button.connect("clicked", self._on_submit)
        button_box.append(self._submit_button)

    def _on_field_changed(self, _entry: Gtk.Editable) -> None:
        full_name = self._name_row.get_text()
        registration = self._registration_row.get_text()

        if full_name.strip() and registration.strip():
            self._username_preview.set_title(preview_username(full_name, registration))
        else:
            self._username_preview.set_title("—")

        result = validate_create_user_fields(full_name, registration)
        self._submit_button.set_sensitive(result.ok)
        self._error_label.set_visible(False)

    def _on_submit(self, _button: Gtk.Button) -> None:
        self._submit_button.set_sensitive(False)
        full_name = self._name_row.get_text()
        registration = self._registration_row.get_text()
        create_user(full_name, registration, self._on_result)

    def _on_result(self, response: HelperResponse) -> None:
        if response.ok:
            self.close()
            self._on_created()
        else:
            self._error_label.set_label(friendly_message(response.code, response.message))
            self._error_label.set_visible(True)
            self._submit_button.set_sensitive(True)
