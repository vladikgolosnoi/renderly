from __future__ import annotations

import os
from pydantic import BaseModel


class Settings(BaseModel):
    expected_cname: str = os.getenv("EXPECTED_CNAME", "pages.renderly.local")
    allow_suffix: str | None = os.getenv("ALLOW_SUFFIX", ".local")
    mock_mode: bool = os.getenv("MOCK_VERIFY", "true").lower() == "true"


settings = Settings()
