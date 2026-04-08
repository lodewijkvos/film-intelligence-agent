from __future__ import annotations

import hashlib
from pathlib import Path
import logging

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from film_intelligence_agent.config.settings import get_settings

logger = logging.getLogger(__name__)


class CachedFetcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.cache_dir = self.settings.raw_cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch_text(self, source_name: str, url: str) -> tuple[str, str]:
        response = httpx.get(
            url,
            headers={
                "User-Agent": "Codex Film Discovery Agent/1.0",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
            timeout=30.0,
            follow_redirects=True,
        )
        response.raise_for_status()
        text = response.text
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        safe_name = source_name.lower().replace(" ", "_").replace("/", "_")
        path = self.cache_dir / f"{safe_name}_{digest}.html"
        path.write_text(text, encoding="utf-8")
        return text, digest
