"""Group membership policy enforced by the privileged helper.

Centralizes which groups a created account may receive and which it must
never receive, regardless of what the rest of the system (e.g.
``/etc/adduser.conf``'s ``EXTRA_GROUPS``) might otherwise inject.
"""

from __future__ import annotations

import grp

FORBIDDEN_GROUPS = {"sudo", "adm", "root", "shadow", "disk", "lxd"}

DEFAULT_EXTRA_GROUPS = ["docker"]

OPTIONAL_GROUPS = ["audio", "video", "render", "plugdev"]


class ForbiddenGroupMembershipError(RuntimeError):
    def __init__(self, username: str, groups: set[str]):
        self.username = username
        self.groups = groups
        super().__init__(
            f"user {username!r} unexpectedly belongs to forbidden group(s): {sorted(groups)}"
        )


def _group_exists(name: str) -> bool:
    try:
        grp.getgrnam(name)
        return True
    except KeyError:
        return False


def resolve_extra_groups() -> tuple[list[str], bool]:
    """Return (groups_to_add, docker_group_available)."""
    groups = [g for g in OPTIONAL_GROUPS if _group_exists(g)]

    docker_available = "docker" in DEFAULT_EXTRA_GROUPS and _group_exists("docker")
    if docker_available:
        groups.append("docker")

    for name in DEFAULT_EXTRA_GROUPS:
        if name != "docker" and _group_exists(name) and name not in groups:
            groups.append(name)

    return groups, docker_available


def current_groups(username: str) -> set[str]:
    groups = {g.gr_name for g in grp.getgrall() if username in g.gr_mem}
    try:
        import pwd

        primary_gid = pwd.getpwnam(username).pw_gid
        groups.add(grp.getgrgid(primary_gid).gr_name)
    except KeyError:
        pass
    return groups


def assert_no_forbidden_groups(username: str) -> None:
    intersection = current_groups(username) & FORBIDDEN_GROUPS
    if intersection:
        raise ForbiddenGroupMembershipError(username, intersection)
