#!/usr/bin/env python3
"""Privileged helper entrypoint.

Invoked exclusively via one of the three Polkit-mapped wrapper scripts
under ``/usr/lib/ubuntu-user-manager/helpers/``, each of which fixes the
operation name (never taken from user input). Reads exactly one JSON line
from stdin, performs the requested operation, and writes exactly one JSON
line to stdout. Never prints a Python traceback to stdout/stderr where the
GUI could surface it to the end user.
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import sys

import operations

MAX_PAYLOAD_BYTES = 8192

ALLOWED_OPERATIONS = {"create-user", "reset-password", "delete-user"}

LOG_PATH = "/var/log/ubuntu-user-manager/helper.log"


def _setup_logging() -> logging.Logger:
    logger = logging.getLogger("user_manager_helper")
    logger.setLevel(logging.INFO)
    try:
        handler = logging.handlers.RotatingFileHandler(
            LOG_PATH, maxBytes=1_000_000, backupCount=3
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        logger.addHandler(handler)
    except OSError:
        logger.addHandler(logging.NullHandler())
    return logger


def _read_payload() -> dict:
    raw = sys.stdin.buffer.read(MAX_PAYLOAD_BYTES + 1)
    if len(raw) > MAX_PAYLOAD_BYTES:
        raise operations.OperationError("PAYLOAD_TOO_LARGE", "Requisição inválida.")
    if not raw:
        raise operations.OperationError("EMPTY_PAYLOAD", "Requisição inválida.")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise operations.OperationError("MALFORMED_PAYLOAD", "Requisição inválida.") from exc
    if not isinstance(data, dict):
        raise operations.OperationError("MALFORMED_PAYLOAD", "Requisição inválida.")
    return data


def _dispatch(op: str, payload: dict) -> dict:
    if op == "create-user":
        return operations.create_user(
            full_name=str(payload.get("full_name", "")),
            registration=str(payload.get("registration", "")),
        )
    if op == "reset-password":
        return operations.reset_password(username=str(payload.get("username", "")))
    if op == "delete-user":
        return operations.delete_user(
            username=str(payload.get("username", "")),
            confirm_registration=str(payload.get("confirm_registration", "")),
        )
    raise operations.OperationError("UNKNOWN_OPERATION", "Operação desconhecida.")


def main() -> int:
    logger = _setup_logging()

    if len(sys.argv) != 2 or sys.argv[1] not in ALLOWED_OPERATIONS:
        print(json.dumps({"status": "error", "code": "UNKNOWN_OPERATION",
                           "message": "Operação desconhecida."}))
        return 1

    op = sys.argv[1]
    username_for_log = None

    try:
        payload = _read_payload()
        username_for_log = payload.get("username")
        result = _dispatch(op, payload)
        username_for_log = result.get("username", username_for_log)
        logger.info("op=%s username=%s success=true", op, username_for_log)
        print(json.dumps(result))
        return 0
    except operations.OperationError as exc:
        logger.info("op=%s username=%s success=false code=%s", op, username_for_log, exc.code)
        print(json.dumps({"status": "error", "code": exc.code, "message": exc.message}))
        return 1
    except Exception:
        logger.exception("op=%s username=%s success=false code=INTERNAL_ERROR", op, username_for_log)
        print(json.dumps({
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": "Ocorreu um erro inesperado ao processar a operação.",
        }))
        return 1


if __name__ == "__main__":
    sys.exit(main())
