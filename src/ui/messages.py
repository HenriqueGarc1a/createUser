"""Maps internal error codes to friendly Portuguese copy.

No technical jargon (useradd, chpasswd, chage, UID, pkexec, Polkit...) is
ever shown to the end user — see spec section 45.
"""

from __future__ import annotations

_MESSAGES = {
    "EMPTY_NAME": "Informe o nome completo.",
    "NAME_TOO_SHORT": "O nome completo é muito curto.",
    "NAME_TOO_LONG": "O nome completo é muito longo.",
    "INVALID_NAME": "O nome completo não pode conter números.",
    "EMPTY_REGISTRATION": "Informe a matrícula.",
    "INVALID_REGISTRATION": "A matrícula deve conter exatamente 8 dígitos numéricos.",
    "INVALID_USERNAME": "Não foi possível gerar um nome de usuário válido a partir desses dados.",
    "USER_ALREADY_EXISTS": "Já existe um usuário com esse nome de usuário.",
    "REGISTRATION_ALREADY_EXISTS": "Já existe um usuário cadastrado com essa matrícula.",
    "USER_NOT_FOUND": "Usuário não encontrado.",
    "NOT_APP_MANAGED": "Este usuário não pode ser gerenciado por aqui.",
    "PROTECTED_ACCOUNT": "Este usuário não pode ser gerenciado por aqui.",
    "REGISTRATION_MISMATCH": "A matrícula informada não confere.",
    "AUTH_CANCELLED": "A autenticação foi cancelada.",
    "AUTH_NOT_AUTHORIZED": "Você não tem permissão para realizar esta ação.",
    "PKEXEC_NOT_FOUND": "O mecanismo de autenticação não está disponível nesta máquina.",
    "HELPER_BAD_RESPONSE": "Ocorreu um erro inesperado. Tente novamente.",
    "INTERNAL_ERROR": "Ocorreu um erro inesperado. Tente novamente.",
    "UNKNOWN_ERROR": "Ocorreu um erro inesperado. Tente novamente.",
}

_DEFAULT_MESSAGE = "Ocorreu um erro inesperado. Tente novamente."


def friendly_message(code: str | None, fallback: str | None = None) -> str:
    if code and code in _MESSAGES:
        return _MESSAGES[code]
    return fallback or _DEFAULT_MESSAGE
