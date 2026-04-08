from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from film_intelligence_agent.parsers.sources.cmf import CMFParser
from film_intelligence_agent.parsers.sources.creative_bc import CreativeBCParser
from film_intelligence_agent.parsers.sources.playback import PlaybackParser
from film_intelligence_agent.parsers.sources.telefilm import TelefilmParser


@dataclass(slots=True)
class SourceDefinition:
    tier: str
    weight: int
    name: str
    source_type: str
    parser_type: str
    url: str


PARSER_MAP = {
    "html_directory": TelefilmParser,
    "program_page_plus_news": TelefilmParser,
    "searchable_database": CMFParser,
    "news_release": PlaybackParser,
    "html_list": CreativeBCParser,
    "article_feed": PlaybackParser,
}


def load_sources(config_path: Path) -> list[SourceDefinition]:
    payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    sources: list[SourceDefinition] = []
    for tier_name, tier_data in payload["source_tiers"].items():
        for source in tier_data["sources"]:
            sources.append(
                SourceDefinition(
                    tier=tier_name,
                    weight=tier_data["weight"],
                    name=source["name"],
                    source_type=source["source_type"],
                    parser_type=source["parser_type"],
                    url=source["url"],
                )
            )
    return sources


def get_parser(parser_type: str):
    return PARSER_MAP[parser_type]()
