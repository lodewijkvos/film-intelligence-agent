from __future__ import annotations

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.integrations.notion.client import get_notion_client


class NotionSetupService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()

    def ensure_databases(self) -> dict[str, str]:
        if not self.settings.notion_parent_page_id:
            raise ValueError("NOTION_PARENT_PAGE_ID is missing.")
        resolved: dict[str, str] = {}
        if self.settings.notion_films_database_id:
            resolved["films_database_id"] = self.settings.notion_films_database_id
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
        return resolved
