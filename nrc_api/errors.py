from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class ApiError(Exception):
    status: int
    code: str
    detail: str
    errors: list[dict[str, Any]] = field(default_factory=list)


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    body: dict[str, Any] = {
        "type": f"https://api.nrc.gov/problems/{exc.code.lower().replace('_', '-')}",
        "title": exc.code.replace("_", " ").title(),
        "status": exc.status,
        "detail": exc.detail,
        "instance": str(request.url.path),
        "code": exc.code,
        "correlation_id": getattr(request.state, "correlation_id", None),
    }
    if exc.errors:
        body["errors"] = exc.errors
    return JSONResponse(body, status_code=exc.status, media_type="application/problem+json")

