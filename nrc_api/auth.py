from __future__ import annotations

import secrets
import uuid
from dataclasses import dataclass

from fastapi import Request

from .config import Settings
from .errors import ApiError


@dataclass(frozen=True, slots=True)
class Principal:
    id: str
    full_name: str
    email: str
    roles: frozenset[str]
    team_ids: tuple[str, ...] = ()
    business_unit_id: str | None = None

    @property
    def is_edo(self) -> bool:
        return "EDO User" in self.roles

    @property
    def is_submitter(self) -> bool:
        return self.is_edo or "Quarterly Performance Submitter" in self.roles


def principal_from_request(request: Request, settings: Settings) -> Principal:
    if settings.dev_auth_enabled:
        user_id = request.headers.get("X-Dev-User-Id", "00000000-0000-4000-8000-000000000001")
        try:
            uuid.UUID(user_id)
        except ValueError as exc:
            raise ApiError(401, "UNAUTHENTICATED", "The development user id is not a UUID.") from exc
        roles = frozenset(filter(None, (x.strip() for x in request.headers.get("X-Dev-Roles", "EDO User").split(","))))
        return Principal(user_id, request.headers.get("X-Dev-Name", "Development User"), request.headers.get("X-Dev-Email", "dev@nrc.gov"), roles)
    proxy_secret = request.headers.get("X-NRC-Proxy-Secret")
    if not settings.trusted_proxy_secret or not secrets.compare_digest(proxy_secret or "", settings.trusted_proxy_secret):
        raise ApiError(401, "UNAUTHENTICATED", "A verified ICAM/Entra session is required.")
    user_id = request.headers.get("X-NRC-User-Id")
    if not user_id:
        raise ApiError(401, "UNAUTHENTICATED", "The identity proxy did not provide a user id.")
    roles = frozenset(filter(None, request.headers.get("X-NRC-Roles", "").split("|")))
    return Principal(user_id, request.headers.get("X-NRC-User-Name", ""), request.headers.get("X-NRC-User-Email", ""), roles)

