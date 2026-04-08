from __future__ import annotations

from sqlalchemy import desc, select

from film_intelligence_agent.config.settings import get_settings
from film_intelligence_agent.db.models import Film, WeeklyReport
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.integrations.notion.client import get_notion_client


class NotionSyncService:
    def __init__(self, films_database_id: str | None = None, people_database_id: str | None = None) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()
        self.films_database_id = films_database_id or self.settings.notion_films_database_id
        self.people_database_id = people_database_id or self.settings.notion_people_database_id

    def sync_films(self, limit: int = 25) -> None:
        if not self.films_database_id:
            return
        with db_session() as session:
            films = list(session.scalars(select(Film).order_by(desc(Film.last_seen_at)).limit(limit)))
        for film in films:
            self.client.pages.create(
                parent={"database_id": self.films_database_id},
                properties={
                    "Title": {"title": [{"text": {"content": film.title}}]},
                    "Status": {"rich_text": [{"text": {"content": film.status or "Unknown"}}]},
                    "Confidence": {"number": film.data_confidence_score},
                    "Opportunity": {"number": film.opportunity_score},
                    "Country": {"rich_text": [{"text": {"content": film.country or "Unknown"}}]},
                    "BudgetRange": {"rich_text": [{"text": {"content": film.budget_text or "Unknown"}}]},
                    "SourceURL": {"url": film.source_url},
                },
            )

    def create_report_page(self, report_id: str) -> str | None:
        if not self.settings.notion_parent_page_id:
            return None
        with db_session() as session:
            report = session.scalar(select(WeeklyReport).where(WeeklyReport.id == report_id))
        if report is None:
            return None
        response = self.client.pages.create(
            parent={"type": "page_id", "page_id": self.settings.notion_parent_page_id},
            properties={
                "title": [{"type": "text", "text": {"content": f"Weekly Report {report.report_date.isoformat()}"}}]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": report.summary_text or ""}}]},
                }
            ],
        )
        return response["id"]
