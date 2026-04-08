from __future__ import annotations

from pathlib import Path

from film_intel_agent.domain.types import ExtractedFilm
from film_intel_agent.fetching.http import CachedFetcher
from film_intel_agent.services.source_registry import get_parser, load_source_definitions


class DiscoveryService:
    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path
        self.fetcher = CachedFetcher()

    def collect(self) -> list[ExtractedFilm]:
        collected: list[ExtractedFilm] = []
        for definition in load_source_definitions(self.config_path):
            fetch_result = self.fetcher.fetch(definition.name, definition.url)
            parser = get_parser(definition.parser_type)
            extracted = parser.parse(
                fetch_result,
                {
                    "name": definition.name,
                    "url": definition.url,
                    "tier": definition.tier,
                    "source_type": definition.source_type,
                    "weight": definition.weight,
                },
            )
            collected.extend(extracted)
        return collected
