"""Username generation and registration-id extraction.

Convention enforced by this app: ``<primeiro_nome>_<matricula>``, e.g.
``henrique_24112345``. Both directions (generate / extract) live here so
the helper can recognize which accounts belong to it before touching them.
"""

from __future__ import annotations

import re
import unicodedata

from utils.validators import REGISTRATION_ID_PATTERN

_INVALID_CHARS_PATTERN = re.compile(r"[^a-z0-9]")


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def slugify_first_name(full_name: str) -> str:
    first_token = full_name.strip().split()[0] if full_name.strip() else ""
    ascii_only = strip_accents(first_token).lower()
    return _INVALID_CHARS_PATTERN.sub("", ascii_only)


def generate_username(full_name: str, registration: str) -> str:
    slug = slugify_first_name(full_name)
    return f"{slug}_{registration.strip()}"


def extract_registration(username: str) -> str | None:
    if "_" not in username:
        return None
    _, _, tail = username.rpartition("_")
    if not REGISTRATION_ID_PATTERN.match(tail):
        return None
    return tail
