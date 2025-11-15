from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from app.api.routes import (
    analytics,
    auth,
    catalog,
    health,
    projects,
    share_links,
    publish,
    themes,
    audit,
    forms,
    templates,
    assets,
    users,
)
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
request_logger = logging.getLogger("renderly.request")

app = FastAPI(
    title=settings.project_name,
    docs_url=f"{settings.api_prefix}/docs",
    openapi_url=f"{settings.api_prefix}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_prefix)
app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(catalog.router, prefix=settings.api_prefix)
app.include_router(projects.router, prefix=settings.api_prefix)
app.include_router(share_links.router, prefix=settings.api_prefix)
app.include_router(share_links.public_router, prefix=settings.api_prefix)
app.include_router(publish.router, prefix=settings.api_prefix)
app.include_router(themes.router, prefix=settings.api_prefix)
app.include_router(audit.router, prefix=settings.api_prefix)
app.include_router(forms.router, prefix=settings.api_prefix)
app.include_router(analytics.router, prefix=settings.api_prefix)
app.include_router(templates.router, prefix=settings.api_prefix)
app.include_router(assets.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    request_logger.info(
        "HTTP %s %s -> %s (%.2f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    return response


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Renderly API", "docs": f"{settings.api_prefix}/docs"}
