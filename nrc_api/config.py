from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    database_path: Path
    environment: str
    dev_auth_enabled: bool
    oidc_issuer: str | None
    oidc_client_id: str | None
    oidc_redirect_uri: str | None
    trusted_proxy_secret: str | None
    rate_limit_per_minute: int
    attachment_directory: Path

    @classmethod
    def from_env(cls) -> "Settings":
        environment = os.getenv("NRC_ENVIRONMENT", "development").lower()
        dev_auth = os.getenv("NRC_DEV_AUTH", "true" if environment == "development" else "false")
        return cls(
            database_path=Path(os.getenv("NRC_DATABASE_PATH", "data/nrc_spa.db")),
            environment=environment,
            dev_auth_enabled=dev_auth.lower() == "true",
            oidc_issuer=os.getenv("NRC_OIDC_ISSUER"),
            oidc_client_id=os.getenv("NRC_OIDC_CLIENT_ID"),
            oidc_redirect_uri=os.getenv("NRC_OIDC_REDIRECT_URI"),
            trusted_proxy_secret=os.getenv("NRC_TRUSTED_PROXY_SECRET"),
            rate_limit_per_minute=int(os.getenv("NRC_RATE_LIMIT_PER_MINUTE", "240")),
            attachment_directory=Path(os.getenv("NRC_ATTACHMENT_DIRECTORY", "data/attachments")),
        )

