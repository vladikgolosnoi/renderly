from __future__ import annotations

from typing import Any

DEFAULT_LOCALE = "ru"


def normalize_code(code: str) -> str:
    return code.strip().lower()


def ensure_locales(settings: dict[str, Any] | None) -> dict[str, Any]:
    settings = settings or {}
    locales = settings.get("locales") or {}
    default_locale = normalize_code(locales.get("default_locale") or DEFAULT_LOCALE)
    configured = locales.get("locales") or [default_locale]
    normalized = []
    for code in configured:
        norm = normalize_code(code)
        if norm and norm not in normalized:
            normalized.append(norm)
    if default_locale not in normalized:
        normalized.insert(0, default_locale)
    locales = {"default_locale": default_locale, "locales": normalized or [default_locale]}
    settings["locales"] = locales
    return locales


def resolve_locale(settings: dict[str, Any] | None, requested: str | None) -> str:
    locales = ensure_locales(settings)
    if requested:
        code = normalize_code(requested)
        if code in locales["locales"]:
            return code
    return locales["default_locale"]


def block_payload_for_locale(
    block: Any,
    locale: str | None,
    settings: dict[str, Any] | None,
) -> dict[str, Any]:
    locales = ensure_locales(settings)
    translations = getattr(block, "translations", None) or {}
    target_locale = locale or locales["default_locale"]
    if target_locale != locales["default_locale"]:
        localized = translations.get(target_locale)
        if localized:
            return localized
    return (block.config or {}) or getattr(block.definition, "default_config", {}) or {}


def sanitize_locale_payload(
    default_locale: str,
    locales: list[str],
) -> dict[str, Any]:
    normalized = []
    for code in locales:
        norm = normalize_code(code)
        if norm and norm not in normalized:
            normalized.append(norm)
    if not normalized:
        normalized = [DEFAULT_LOCALE]
    norm_default = normalize_code(default_locale or normalized[0])
    if norm_default not in normalized:
        normalized.insert(0, norm_default)
    return {"default_locale": norm_default, "locales": normalized}
