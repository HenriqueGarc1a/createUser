"""Thin wrappers around the Linux user-management commands.

Every call uses an argument list (never a shell string) so there is no
command-injection surface. Passwords are never passed as process
arguments — they travel over ``chpasswd``'s stdin only.
"""

from __future__ import annotations

import os
import subprocess

USERADD = "/usr/sbin/useradd"
USERDEL = "/usr/sbin/userdel"
USERMOD = "/usr/sbin/usermod"
CHAGE = "/usr/bin/chage"
CHPASSWD = "/usr/sbin/chpasswd"
GETENT = "/usr/bin/getent"


class CommandError(RuntimeError):
    def __init__(self, command: list[str], returncode: int, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(f"command {command[0]} failed ({returncode}): {stderr.strip()}")


def _run(command: list[str], input_data: bytes | None = None) -> subprocess.CompletedProcess:
    result = subprocess.run(
        command,
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        raise CommandError(command, result.returncode, result.stderr.decode(errors="replace"))
    return result


def user_exists(username: str) -> bool:
    result = subprocess.run(
        [GETENT, "passwd", username],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def create_user(username: str, full_name: str) -> None:
    _run([USERADD, "-m", "-c", full_name, "-s", "/bin/bash", username])


def restrict_home_directory(username: str) -> None:
    """Lock the home directory down to owner-only access, matching the
    hardening the previous manual creation script applied."""
    os.chmod(f"/home/{username}", 0o700)


def delete_user(username: str) -> None:
    _run([USERDEL, username])


def add_to_groups(username: str, groups: list[str]) -> None:
    if not groups:
        return
    _run([USERMOD, "-aG", ",".join(groups), username])


def expire_password(username: str) -> None:
    _run([CHAGE, "-d", "0", username])


def set_password_via_chpasswd(username: str, password: str) -> None:
    payload = f"{username}:{password}\n".encode()
    _run([CHPASSWD], input_data=payload)
