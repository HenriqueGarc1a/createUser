"""Shared validation rules for user data.

Single source of truth for the registration-id (matrícula) digit-count rule
and other field validations. Imported by both the unprivileged GUI (for
inline feedback) and the privileged helper (for authoritative
re-validation) — the helper is a separately frozen PyInstaller build but
compiles from this same source file, so there is exactly one place to
change the rule.
"""

from __future__ import annotations

import re
from typing import NamedTuple, Optional

REGISTRATION_ID_LENGTH = 8
REGISTRATION_ID_PATTERN = re.compile(rf"^\d{{{REGISTRATION_ID_LENGTH}}}$")

USERNAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")

MIN_FULL_NAME_LENGTH = 2
MAX_FULL_NAME_LENGTH = 128

FULL_NAME_ALLOWED_PATTERN = re.compile(r"^[^\d]+$")


class ValidationResult(NamedTuple):
    ok: bool
    code: Optional[str] = None
    message: Optional[str] = None


def validate_full_name(name: str) -> ValidationResult:
    name = name.strip()
    if not name:
        return ValidationResult(False, "EMPTY_NAME", "O nome completo é obrigatório.")
    if len(name) < MIN_FULL_NAME_LENGTH:
        return ValidationResult(False, "NAME_TOO_SHORT", "O nome completo é muito curto.")
    if len(name) > MAX_FULL_NAME_LENGTH:
        return ValidationResult(False, "NAME_TOO_LONG", "O nome completo é muito longo.")
    if not FULL_NAME_ALLOWED_PATTERN.match(name):
        return ValidationResult(False, "INVALID_NAME", "O nome completo não pode conter números.")
    return ValidationResult(True)


def validate_registration_id(value: str) -> ValidationResult:
    value = value.strip()
    if not value:
        return ValidationResult(False, "EMPTY_REGISTRATION", "A matrícula é obrigatória.")
    if not REGISTRATION_ID_PATTERN.match(value):
        return ValidationResult(
            False,
            "INVALID_REGISTRATION",
            f"A matrícula deve conter exatamente {REGISTRATION_ID_LENGTH} dígitos numéricos.",
        )
    return ValidationResult(True)


def validate_username(value: str) -> ValidationResult:
    if not value:
        return ValidationResult(False, "EMPTY_USERNAME", "O nome de usuário é obrigatório.")
    if len(value) > 32:
        return ValidationResult(False, "USERNAME_TOO_LONG", "O nome de usuário é muito longo.")
    if not USERNAME_PATTERN.match(value):
        return ValidationResult(False, "INVALID_USERNAME", "O nome de usuário gerado é inválido.")
    return ValidationResult(True)
