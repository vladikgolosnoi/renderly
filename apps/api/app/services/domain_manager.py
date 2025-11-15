from __future__ import annotations

import httpx

from app.core.config import settings


class DomainVerificationError(RuntimeError):
    ...


def verify_domain(hostname: str, token: str) -> tuple[str, str]:
    """
    Returns tuple(status, message)
    """
    payload = {
        "domain": hostname,
        "expected_cname": settings.custom_domain_cname_target,
        "token": token,
    }
    try:
        response = httpx.post(f"{settings.domain_manager_url.rstrip('/')}/verify", json=payload, timeout=5.0)
    except httpx.HTTPError as exc:
        raise DomainVerificationError(str(exc)) from exc
    if response.status_code >= 400:
        raise DomainVerificationError(response.text)
    data = response.json()
    return data.get("status", "pending"), data.get("message", "")
