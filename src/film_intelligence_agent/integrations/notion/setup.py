from __future__ import annotations

import logging

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.integrations.notion.client import get_notion_client
from film_intelligence_agent.services.config_store import ConfigStore

logger = logging.getLogger(__name__)


class NotionSetupService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()
        self.config_store = ConfigStore()

    def ensure_databases(self) -> dict[str, str]:
        if not self.settings.notion_parent_page_id:
            raise ValueError("NOTION_PARENT_PAGE_ID is missing.")
        resolved: dict[str, str] = {}
        stored_films_id = self.config_store.get("notion_films_database_id")
        stored_people_id = self.config_store.get("notion_people_database_id")
        resolved["films_database_id"] = self._ensure_database(
            preferred_id=self.settings.notion_films_database_id or stored_films_id,
            title="Film Opportunities",
            properties={
                "Title": {"title": {}},
                "Status": {"rich_text": {}},
                "Confidence": {"number": {}},
                "Opportunity": {"number": {}},
                "Country": {"rich_text": {}},
                "BudgetRange": {"rich_text": {}},
                "SourceURL": {"url": {}},
            },
        )
        resolved["people_database_id"] = self._ensure_database(
            preferred_id=self.settings.notion_people_database_id or stored_people_id,
            title="People Collaborators",
            properties={
                "Name": {"title": {}},
                "IMDbURL": {"url": {}},
                "KnownCollaborator": {"checkbox": {}},
                "SharedProjects": {"rich_text": {}},
                "SharedProjectCount": {"number": {}},
            },
        )
        if "films_database_id" in resolved:
            self.config_store.set("notion_films_database_id", resolved["films_database_id"])
        if "people_database_id" in resolved:
            self.config_store.set("notion_people_database_id", resolved["people_database_id"])
        logger.info(
            "Notion database ids resolved: films=%s people=%s",
            resolved.get("films_database_id"),
            resolved.get("people_database_id"),
        )
        return resolved

    def _ensure_database(self, preferred_id: str | None, title: str, properties: dict) -> str:
        if preferred_id and self._is_valid_database(preferred_id):
            return preferred_id
        if preferred_id:
            logger.warning("Stored Notion database id %s for %s is invalid; creating a fresh database", preferred_id, title)
        response = self.client.databases.create(
            parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            properties=properties,
        )
        return response["id"]

    def _is_valid_database(self, database_id: str) -> bool:
        try:
            database = self.client.databases.retrieve(database_id=database_id)
        except Exception:
            return False
        properties = database.get("properties", {}) or {}
        if not isinstance(properties, dict) or not properties:
            return False
        return any(meta.get("type") == "title" for meta in properties.values())
