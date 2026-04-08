from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from film_intel_agent.parsers.sources.cmf import CMFParser
from film_intel_agent.parsers.sources.creative_bc import CreativeBCParser
from film_intel_agent.parsers.sources.playback import PlaybackParser
from film_intel_agent.parsers.sources.telefilm import TelefilmDirectoryParser


PARSER_MAP = {
    "html_directory": TelefilmDirectoryParser,
    "searchable_database": CMFParser,
    "html_list": CreativeBCParser,
    "article_feed": PlaybackParser,
    "news_release": PlaybackParser,
    "program_page_plus_news": CreativeBCParser,
}


@dataclass(slots=True)
class SourceDefinition:
    tier: str
    weight: int
    name: str
    source_type: str
    parser_type: str
    url: str


def load_source_definitions(config_path: Path) -> list[SourceDefinition]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    definitions: list[SourceDefinition] = []
    for tier_name, tier_payload in raw["source_tiers"].items():
        for source in tier_payload["sources"]:
            definitions.append(
                SourceDefinition(
                    tier=tier_name,
                    weight=tier_payload["weight"],
                    name=source["name"],
                    source_type=source["source_type"],
                    parser_type=source["parser_type"],
                    url=source["url"],
                )
            )
    return definitions


def get_parser(parser_type: str):
    parser_cls = PARSER_MAP[parser_type]
    return parser_cls()
