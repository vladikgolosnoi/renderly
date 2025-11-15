from __future__ import annotations

from pathlib import Path

from app.core.config import settings


def persist_domain_html(hostname: str, html: str) -> None:
    base = settings.custom_domain_local_dir
    if not base:
        return
    root = Path(base)
    try:
        target_dir = root / hostname
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "index.html").write_text(html, encoding="utf-8")
    except OSError:
        # local storage is best-effort
        return


def remove_domain_html(hostname: str) -> None:
    base = settings.custom_domain_local_dir
    if not base:
        return
    target_dir = Path(base) / hostname
    try:
        if target_dir.exists():
            for child in target_dir.iterdir():
                child.unlink(missing_ok=True)  # type: ignore[arg-type]
            target_dir.rmdir()
    except OSError:
        return
