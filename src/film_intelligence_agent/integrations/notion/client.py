from __future__ import annotations

from notion_client import Client

from film_intelligence_agent.config.settings import get_settings


def get_notion_client() -> Client:
    token = get_settings().notion_token
    if not token:
        raise ValueError("NOTION_TOKEN is missing.")
    return Client(auth=token)
