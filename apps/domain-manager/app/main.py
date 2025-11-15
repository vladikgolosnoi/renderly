from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import dns.resolver

from .config import settings

app = FastAPI(title="Domain Manager", version="0.1.0")


class VerifyRequest(BaseModel):
    domain: str = Field(..., example="landing.example.edu")
    expected_cname: str
    token: str


@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/verify")
def verify(request: VerifyRequest) -> dict[str, str]:
    domain = request.domain.lower().strip()
    if settings.mock_mode and settings.allow_suffix and domain.endswith(settings.allow_suffix):
        return {"status": "verified", "message": "Mock suffix accepted"}
    try:
        answers = dns.resolver.resolve(domain, "CNAME")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"DNS lookup failed: {exc}") from exc
    targets = {str(answer.target).rstrip(".").lower() for answer in answers}
    expected = request.expected_cname.rstrip(".").lower()
    if expected in targets:
        return {"status": "verified", "message": f"CNAME points to {expected}"}
    raise HTTPException(
        status_code=422,
        detail=f"CNAME mismatch. Found {', '.join(targets) or 'none'}, expected {expected}",
    )
