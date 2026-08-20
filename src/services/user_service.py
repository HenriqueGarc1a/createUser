"""Facade used by the UI: read-only listing (no Polkit) plus the
create/reset/delete operations (delegated to privileged_service)."""

from __future__ import annotations

import pwd
from dataclasses import dataclass
from typing import Callable

from services.privileged_service import HelperResponse, run_privileged_operation_async
from utils.username import extract_registration, generate_username
from utils.validators import validate_full_name, validate_registration_id

HUMAN_UID_MIN = 1000
HUMAN_UID_MAX = 59999

# Belt-and-suspenders blacklist in addition to the UID-range filter, in
# case a lab image has a human-looking system account outside the usual
# UID range.
SYSTEM_ACCOUNT_NAMES = {
    "root", "daemon", "bin", "sys", "sync", "games", "man", "lp", "mail",
    "news", "uucp", "proxy", "www-data", "backup", "list", "irc", "gnats",
    "nobody",
}


@dataclass
class UserRecord:
    full_name: str
    username: str
    registration: str | None
    uid: int


def _is_system_account(name: str) -> bool:
    return name in SYSTEM_ACCOUNT_NAMES or name.startswith("systemd-")


def list_users(query: str | None = None) -> list[UserRecord]:
    records: list[UserRecord] = []
    for entry in pwd.getpwall():
        if not (HUMAN_UID_MIN <= entry.pw_uid <= HUMAN_UID_MAX):
            continue
        if _is_system_account(entry.pw_name):
            continue
        registration = extract_registration(entry.pw_name)
        full_name = entry.pw_gecos.split(",")[0] or entry.pw_name
        records.append(UserRecord(full_name, entry.pw_name, registration, entry.pw_uid))

    records.sort(key=lambda r: r.full_name.lower())

    if not query:
        return records

    needle = query.strip().lower()
    return [
        r
        for r in records
        if needle in r.full_name.lower()
        or needle in r.username.lower()
        or (r.registration and needle in r.registration)
    ]


def preview_username(full_name: str, registration: str) -> str:
    return generate_username(full_name, registration)


def validate_create_user_fields(full_name: str, registration: str):
    name_result = validate_full_name(full_name)
    if not name_result.ok:
        return name_result
    return validate_registration_id(registration)


def create_user(full_name: str, registration: str, callback: Callable[[HelperResponse], None]) -> None:
    run_privileged_operation_async(
        "create-user",
        {"full_name": full_name.strip(), "registration": registration.strip()},
        callback,
    )


def reset_password(username: str, callback: Callable[[HelperResponse], None]) -> None:
    run_privileged_operation_async("reset-password", {"username": username}, callback)


def delete_user(
    username: str, confirm_registration: str, callback: Callable[[HelperResponse], None]
) -> None:
    run_privileged_operation_async(
        "delete-user",
        {"username": username, "confirm_registration": confirm_registration.strip()},
        callback,
    )
