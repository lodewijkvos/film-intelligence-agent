from __future__ import annotations

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.integrations.notion.client import get_notion_client
from film_intelligence_agent.services.config_store import ConfigStore


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
        if self.settings.notion_films_database_id:
            resolved["films_database_id"] = self.settings.notion_films_database_id
        elif stored_films_id:
            resolved["films_database_id"] = stored_films_id
        else:
            existing = self._find_child_database("Film Opportunities")
            if existing:
                resolved["films_database_id"] = existing
            else:
                response = self.client.databases.create(
                    parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
                    title=[{"type": "text", "text": {"content": "Film Opportunities"}}],
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
                resolved["films_database_id"] = response["id"]
        if self.settings.notion_people_database_id:
            resolved["people_database_id"] = self.settings.notion_people_database_id
        elif stored_people_id:
            resolved["people_database_id"] = stored_people_id
        else:
            existing = self._find_child_database("People Collaborators")
            if existing:
                resolved["people_database_id"] = existing
            else:
                response = self.client.databases.create(
                    parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
                    title=[{"type": "text", "text": {"content": "People Collaborators"}}],
                    properties={
                        "Name": {"title": {}},
                        "IMDbURL": {"url": {}},
                        "KnownCollaborator": {"checkbox": {}},
                        "SharedProjects": {"rich_text": {}},
                        "SharedProjectCount": {"number": {}},
                    },
                )
                resolved["people_database_id"] = response["id"]
        if "films_database_id" in resolved:
            self.config_store.set("notion_films_database_id", resolved["films_database_id"])
        if "people_database_id" in resolved:
            self.config_store.set("notion_people_database_id", resolved["people_database_id"])
        return resolved

    def _find_child_database(self, expected_title: str) -> str | None:
        response = self.client.search(
            query=expected_title,
            filter={"value": "data_source", "property": "object"},
        )
        for result in response.get("results", []):
            parent = result.get("parent", {})
            if parent.get("type") != "page_id":
                continue
            if parent.get("page_id") != self.settings.notion_parent_page_id:
                continue
            titles = result.get("title", [])
            title = "".join(part.get("plain_text", "") for part in titles).strip()
            if title == expected_title:
                return result["id"]
        return None
