from __future__ import annotations

from film_intel_agent.config.settings import get_settings
from film_intel_agent.integrations.notion.client import get_notion_client


class NotionSetupService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()

    def ensure_core_databases(self) -> dict[str, str]:
        if not self.settings.notion_parent_page_id:
            raise ValueError("NOTION_PARENT_PAGE_ID is required to create Notion databases.")

        created: dict[str, str] = {}
        if not self.settings.notion_films_database_id:
            response = self.client.databases.create(
                parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
                title=[{"type": "text", "text": {"content": "Film Opportunities"}}],
                properties={
                    "Title": {"title": {}},
                    "Status": {"rich_text": {}},
                    "Confidence": {"number": {}},
                    "Opportunity": {"number": {}},
                    "Country": {"rich_text": {}},
                    "ProvinceOrState": {"rich_text": {}},
                    "Company": {"rich_text": {}},
                    "Producer": {"rich_text": {}},
                    "Director": {"rich_text": {}},
                    "Editor": {"rich_text": {}},
                    "FundingSource": {"rich_text": {}},
                    "FundingProgram": {"rich_text": {}},
                    "FundingAmount": {"number": {}},
                    "BudgetRange": {"rich_text": {}},
                    "Source": {"rich_text": {}},
                    "SourceURL": {"url": {}},
                    "DateDetected": {"date": {}},
                    "Notes": {"rich_text": {}},
                },
            )
            created["films_database_id"] = response["id"]
        if not self.settings.notion_people_database_id:
            response = self.client.databases.create(
                parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
                title=[{"type": "text", "text": {"content": "People Collaborators"}}],
                properties={
                    "Name": {"title": {}},
                    "IMDbURL": {"url": {}},
                    "KnownCollaborator": {"checkbox": {}},
                    "SharedProjects": {"rich_text": {}},
                    "SharedProjectCount": {"number": {}},
                    "MatchConfidence": {"number": {}},
                    "MatchMethod": {"rich_text": {}},
                    "Notes": {"rich_text": {}},
                },
            )
            created["people_database_id"] = response["id"]
        return created
