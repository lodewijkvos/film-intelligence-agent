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
        resolved_existing_id = self._resolve_usable_data_source_id(preferred_id) if preferred_id else None
        if resolved_existing_id:
            return resolved_existing_id
        if preferred_id:
            logger.warning("Stored Notion database id %s for %s is invalid; creating a fresh database", preferred_id, title)
        response = self.client.databases.create(
            parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
            title=[{"type": "text", "text": {"content": title}}],
            initial_data_source={"properties": properties},
        )
        return self._extract_data_source_id(response) or response["id"]

    def _resolve_usable_data_source_id(self, object_id: str | None) -> str | None:
        if not object_id:
            return None
        try:
            data_source = self.client.data_sources.retrieve(data_source_id=object_id)
            properties = data_source.get("properties", {}) or {}
            if isinstance(properties, dict) and any(meta.get("type") == "title" for meta in properties.values()):
                return object_id
        except Exception:
            pass
        try:
            database = self.client.databases.retrieve(database_id=object_id)
        except Exception:
            return None
        return self._extract_data_source_id(database)

    def _extract_data_source_id(self, response: dict) -> str | None:
        data_sources = response.get("data_sources", []) or []
        if data_sources:
            return data_sources[0].get("id")
        return None
