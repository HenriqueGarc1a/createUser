"""Main window: search, list, and the '+ Criar usuário' entry point."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from services.user_service import UserRecord, list_users
from ui.create_user_dialog import CreateUserDialog
from ui.delete_user_dialog import DeleteUserDialog
from ui.reset_password_dialog import show_reset_password_dialog
from ui.user_row import UserRow


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, application: Adw.Application):
        super().__init__(application=application, default_width=560, default_height=640)
        self.set_title("Ubuntu User Manager")

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        header_bar = Adw.HeaderBar()
        toolbar_view.add_top_bar(header_bar)

        toast_overlay = Adw.ToastOverlay()
        toolbar_view.set_content(toast_overlay)
        self._toast_overlay = toast_overlay

        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        toast_overlay.set_child(root_box)

        self._search_entry = Gtk.SearchEntry(
            placeholder_text="Buscar usuário...",
            margin_start=12,
            margin_end=12,
            margin_top=12,
        )
        self._search_entry.connect("search-changed", self._on_search_changed)
        root_box.append(self._search_entry)

        scrolled = Gtk.ScrolledWindow(vexpand=True)
        root_box.append(scrolled)

        clamp = Adw.Clamp(margin_start=12, margin_end=12, margin_bottom=12)
        scrolled.set_child(clamp)

        self._list_box = Gtk.ListBox(css_classes=["boxed-list"], valign=Gtk.Align.START)
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        clamp.set_child(self._list_box)

        self._empty_status = Adw.StatusPage(
            title="Nenhum usuário encontrado",
            icon_name="system-users-symbolic",
            visible=False,
        )
        root_box.append(self._empty_status)

        create_button = Gtk.Button(
            label="+ Criar usuário",
            halign=Gtk.Align.CENTER,
            margin_bottom=18,
        )
        create_button.add_css_class("suggested-action")
        create_button.add_css_class("pill")
        create_button.connect("clicked", self._on_create_clicked)
        root_box.append(create_button)

        self.refresh()

    def refresh(self) -> None:
        query = self._search_entry.get_text()
        records = list_users(query)

        child = self._list_box.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self._list_box.remove(child)
            child = next_child

        for record in records:
            row = UserRow(record, self._on_reset_password, self._on_delete)
            self._list_box.append(row)

        has_results = bool(records)
        self._list_box.set_visible(has_results)
        self._empty_status.set_visible(not has_results)

    def _on_search_changed(self, _entry: Gtk.SearchEntry) -> None:
        self.refresh()

    def _on_create_clicked(self, _button: Gtk.Button) -> None:
        dialog = CreateUserDialog(self, self._on_user_created)
        dialog.present()

    def _on_user_created(self) -> None:
        self.refresh()
        self._toast_overlay.add_toast(Adw.Toast(title="Usuário criado com sucesso"))

    def _on_reset_password(self, record: UserRecord) -> None:
        show_reset_password_dialog(self, record, self._on_password_reset)

    def _on_password_reset(self) -> None:
        self._toast_overlay.add_toast(Adw.Toast(title="Senha resetada"))

    def _on_delete(self, record: UserRecord) -> None:
        dialog = DeleteUserDialog(self, record, self._on_user_deleted)
        dialog.present()

    def _on_user_deleted(self) -> None:
        self.refresh()
        self._toast_overlay.add_toast(Adw.Toast(title="Usuário removido"))
