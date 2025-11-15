from __future__ import annotations

import re
from unicodedata import normalize

CYRILLIC_MAP = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "yo",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "i",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def _transliterate(value: str) -> str:
    result = []
    for char in value:
        lower = char.lower()
        mapped = CYRILLIC_MAP.get(lower)
        if mapped is None:
            result.append(char)
        else:
            result.append(mapped if char.islower() else mapped.upper())
    return "".join(result)


def slugify(value: str) -> str:
    transliterated = _transliterate(value)
    transliterated = normalize("NFKD", transliterated).encode("ascii", "ignore").decode("ascii")
    transliterated = re.sub(r"[^a-zA-Z0-9]+", "-", transliterated).strip("-").lower()
    return transliterated or "template"
