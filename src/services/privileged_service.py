"""Bridge between the GUI and the privileged helper, via pkexec + Polkit.

Each privileged action maps to its own thin wrapper executable (see
``helper/entrypoints/``) because Polkit resolves the action ID to check by
matching the *executable path* pkexec is asked to run, not by any
argument — a single shared helper path would be ambiguous across the
three actions.
"""

from __future__ import annotations

import json
import subprocess
import threading
from dataclasses import dataclass
from typing import Callable, Literal

import gi

gi.require_version("GLib", "2.0")
from gi.repository import GLib

PrivilegedAction = Literal["create-user", "reset-password", "delete-user"]

_WRAPPER_PATHS: dict[str, str] = {
    "create-user": "/usr/lib/ubuntu-user-manager/helpers/create-user",
    "reset-password": "/usr/lib/ubuntu-user-manager/helpers/reset-password",
    "delete-user": "/usr/lib/ubuntu-user-manager/helpers/delete-user",
}

PKEXEC_CANCELLED = 126
PKEXEC_NOT_AUTHORIZED = 127


@dataclass
class HelperResponse:
    ok: bool
    data: dict
    code: str | None = None
    message: str | None = None


def _call_helper(action: PrivilegedAction, payload: dict) -> HelperResponse:
    wrapper = _WRAPPER_PATHS[action]

    try:
        process = subprocess.Popen(
            ["pkexec", wrapper],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return HelperResponse(
            False, {}, "PKEXEC_NOT_FOUND", "O mecanismo de autenticação não está disponível."
        )

    stdout, stderr = process.communicate(json.dumps(payload).encode("utf-8"))

    if process.returncode == PKEXEC_CANCELLED:
        return HelperResponse(False, {}, "AUTH_CANCELLED", "Autenticação cancelada.")
    if process.returncode == PKEXEC_NOT_AUTHORIZED:
        return HelperResponse(False, {}, "AUTH_NOT_AUTHORIZED", "Autenticação não autorizada.")

    try:
        result = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return HelperResponse(
            False, {}, "HELPER_BAD_RESPONSE", "Resposta inválida do serviço privilegiado."
        )

    if result.get("status") == "ok":
        return HelperResponse(True, result)

    return HelperResponse(
        False, {}, result.get("code", "UNKNOWN_ERROR"), result.get("message", "Erro desconhecido.")
    )


def run_privileged_operation_async(
    action: PrivilegedAction, payload: dict, callback: Callable[[HelperResponse], None]
) -> None:
    """Run the privileged call on a worker thread; deliver the result on
    the GTK main loop via GLib.idle_add so the UI stays responsive while
    the Polkit graphical prompt is open."""

    def worker() -> None:
        response = _call_helper(action, payload)
        GLib.idle_add(callback, response)

    threading.Thread(target=worker, daemon=True).start()
