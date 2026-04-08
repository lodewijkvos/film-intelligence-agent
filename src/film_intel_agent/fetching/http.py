from __future__ import annotations

import hashlib
import logging
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_fixed

from film_intel_agent.config.settings import get_settings
from film_intel_agent.domain.types import RawFetchResult

logger = logging.getLogger(__name__)


class CachedFetcher:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.cache_root = self.settings.raw_cache_dir
        self.cache_root.mkdir(parents=True, exist_ok=True)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), reraise=True)
    def fetch(self, source_name: str, source_url: str) -> RawFetchResult:
        headers = {"User-Agent": "Codex Film Discovery Agent/1.0"}
        with httpx.Client(timeout=30.0, follow_redirects=True, headers=headers) as client:
            response = client.get(source_url)
            response.raise_for_status()

        html = response.text
        snapshot_hash = hashlib.sha256(html.encode("utf-8")).hexdigest()
        cache_path = self._cache_snapshot(source_name, snapshot_hash, html)
        logger.info("Fetched %s", source_url)
        return RawFetchResult(
            source_name=source_name,
            source_url=source_url,
            status_code=response.status_code,
            content_type=response.headers.get("content-type"),
            html=html,
            text=response.text,
            snapshot_hash=snapshot_hash,
            cache_path=str(cache_path),
        )

    def _cache_snapshot(self, source_name: str, snapshot_hash: str, html: str) -> Path:
        safe_name = source_name.lower().replace(" ", "_").replace("/", "_")
        path = self.cache_root / safe_name
        path.mkdir(parents=True, exist_ok=True)
        target = path / f"{snapshot_hash}.html"
        target.write_text(html, encoding="utf-8")
        return target
