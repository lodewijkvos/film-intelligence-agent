from __future__ import annotations

from notion_client import Client

from film_intel_agent.config.settings import get_settings


def get_notion_client() -> Client:
    settings = get_settings()
    if not settings.notion_token:
        raise ValueError("NOTION_TOKEN is not configured")
    return Client(auth=settings.notion_token)
