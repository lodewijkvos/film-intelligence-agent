from __future__ import annotations

from pathlib import Path
import logging

from film_intelligence_agent.domain.types import ExtractedFilm
from film_intelligence_agent.fetching.http import CachedFetcher
from film_intelligence_agent.services.source_registry import get_parser, load_sources

logger = logging.getLogger(__name__)


class DiscoveryService:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.fetcher = CachedFetcher()

    def collect(self) -> list[ExtractedFilm]:
        collected: list[ExtractedFilm] = []
        for source in load_sources(self.config_path):
            try:
                html, _digest = self.fetcher.fetch_text(source.name, source.url)
                parser = get_parser(source.parser_type)
                collected.extend(
                    parser.parse(
                        html,
                        {
                            "name": source.name,
                            "url": source.url,
                            "tier": source.tier,
                            "source_type": source.source_type,
                            "weight": source.weight,
                        },
                    )
                )
            except Exception as exc:
                logger.warning("Skipping source %s due to fetch/parse failure: %s", source.name, exc)
        return collected
