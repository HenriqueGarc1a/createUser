"""'Resetar senha' confirmation — spec section 16."""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk

from services.privileged_service import HelperResponse
from services.user_service import UserRecord, reset_password
from ui.messages import friendly_message


def show_reset_password_dialog(
    parent: Gtk.Window, record: UserRecord, on_reset: Callable[[], None]
) -> None:
    new_password = record.registration or "—"

    dialog = Adw.MessageDialog(
        transient_for=parent,
        heading=f"Resetar senha de {record.full_name}?",
        body=(
            f"A senha será redefinida para:\n\n{new_password}\n\n"
            "O usuário será obrigado a definir uma nova senha no próximo login."
        ),
    )
    dialog.add_response("cancel", "Cancelar")
    dialog.add_response("reset", "Resetar senha")
    dialog.set_response_appearance("reset", Adw.ResponseAppearance.SUGGESTED)
    dialog.set_default_response("cancel")
    dialog.set_close_response("cancel")

    def on_response(_dlg: Adw.MessageDialog, response: str) -> None:
        if response != "reset":
            return

        def handle_result(result: HelperResponse) -> None:
            if result.ok:
                on_reset()
            else:
                error_dialog = Adw.MessageDialog(
                    transient_for=parent,
                    heading="Não foi possível resetar a senha",
                    body=friendly_message(result.code, result.message),
                )
                error_dialog.add_response("ok", "OK")
                error_dialog.present()

        reset_password(record.username, handle_result)

    dialog.connect("response", on_response)
    dialog.present()
