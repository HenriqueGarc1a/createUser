"""Privileged operations: create, reset-password, delete.

Called only by ``user_manager_helper.py`` after it has already parsed the
JSON request from stdin. Every field is re-validated here — the GUI's
validation is only for UX, this module is the actual authority.
"""

from __future__ import annotations

import pwd

import linux_users
from groups_policy import (
    FORBIDDEN_GROUPS,
    assert_no_forbidden_groups,
    current_groups,
    resolve_extra_groups,
)
from utils.username import extract_registration, generate_username
from utils.validators import validate_full_name, validate_registration_id, validate_username

HUMAN_UID_MIN = 1000
HUMAN_UID_MAX = 59999


class OperationError(RuntimeError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


def _require(result, field_error_code_prefix: str = "") -> None:
    if not result.ok:
        raise OperationError(result.code, result.message)


def _list_app_managed_registrations() -> set[str]:
    registrations = set()
    for entry in pwd.getpwall():
        if HUMAN_UID_MIN <= entry.pw_uid <= HUMAN_UID_MAX:
            reg = extract_registration(entry.pw_name)
            if reg:
                registrations.add(reg)
    return registrations


def create_user(full_name: str, registration: str) -> dict:
    full_name = full_name.strip()
    registration = registration.strip()

    _require(validate_full_name(full_name))
    _require(validate_registration_id(registration))

    username = generate_username(full_name, registration)
    _require(validate_username(username))

    if linux_users.user_exists(username):
        raise OperationError("USER_ALREADY_EXISTS", f"O usuário {username!r} já existe.")

    if registration in _list_app_managed_registrations():
        raise OperationError(
            "REGISTRATION_ALREADY_EXISTS", f"A matrícula {registration!r} já está em uso."
        )

    linux_users.create_user(username, full_name)

    try:
        linux_users.restrict_home_directory(username)
        linux_users.set_password_via_chpasswd(username, registration)
        linux_users.expire_password(username)

        extra_groups, docker_available = resolve_extra_groups()
        linux_users.add_to_groups(username, extra_groups)

        assert_no_forbidden_groups(username)
    except Exception:
        try:
            linux_users.delete_user(username)
        except Exception:
            pass
        raise

    return {
        "status": "ok",
        "username": username,
        "full_name": full_name,
        "registration": registration,
        "home": f"/home/{username}",
        "docker_group_available": docker_available,
    }


def _validate_managed_account(username: str) -> str:
    if not linux_users.user_exists(username):
        raise OperationError("USER_NOT_FOUND", f"O usuário {username!r} não foi encontrado.")

    registration = extract_registration(username)
    if registration is None:
        raise OperationError(
            "NOT_APP_MANAGED", f"O usuário {username!r} não foi criado por esta aplicação."
        )

    if current_groups(username) & FORBIDDEN_GROUPS:
        raise OperationError(
            "PROTECTED_ACCOUNT", f"O usuário {username!r} não pode ser gerenciado por aqui."
        )

    return registration


def reset_password(username: str) -> dict:
    registration = _validate_managed_account(username)

    linux_users.set_password_via_chpasswd(username, registration)
    linux_users.expire_password(username)

    return {"status": "ok", "username": username, "registration": registration}


def delete_user(username: str, confirm_registration: str) -> dict:
    registration = _validate_managed_account(username)

    if confirm_registration.strip() != registration:
        raise OperationError(
            "REGISTRATION_MISMATCH", "A matrícula informada não confere para confirmar a exclusão."
        )

    linux_users.delete_user(username)

    return {"status": "ok", "username": username, "home": f"/home/{username}"}
