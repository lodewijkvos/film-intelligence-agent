from __future__ import annotations

from sqlalchemy import desc, select

from film_intel_agent.config.settings import get_settings
from film_intel_agent.db.models import Film, WeeklyReport
from film_intel_agent.db.session import db_session
from film_intel_agent.integrations.notion.client import get_notion_client


class NotionSyncService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = get_notion_client()

    def sync_latest_films(self, limit: int = 25) -> None:
        if not self.settings.notion_films_database_id:
            return
        with db_session() as session:
            films = list(session.scalars(select(Film).order_by(desc(Film.last_seen_at)).limit(limit)))
        for film in films:
            self.client.pages.create(
                parent={"database_id": self.settings.notion_films_database_id},
                properties={
                    "Title": {"title": [{"text": {"content": film.title}}]},
                    "Status": {"rich_text": [{"text": {"content": film.status or "Unknown"}}]},
                    "Confidence": {"number": film.data_confidence_score},
                    "Opportunity": {"number": film.opportunity_score},
                    "Country": {"rich_text": [{"text": {"content": film.country or "Unknown"}}]},
                    "Company": {
                        "rich_text": [{"text": {"content": film.production_company or "Unknown"}}]
                    },
                    "BudgetRange": {"rich_text": [{"text": {"content": film.budget_text or "Unknown"}}]},
                    "Source": {"rich_text": [{"text": {"content": film.source_name}}]},
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
                "title": [
                    {
                        "type": "text",
                        "text": {
                            "content": f"Weekly Report {report.report_date.isoformat()}",
                        },
                    }
                ]
            },
            children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {"content": report.summary_text or "Weekly report generated."},
                            }
                        ]
                    },
                }
            ],
        )
        with db_session() as session:
            report = session.scalar(select(WeeklyReport).where(WeeklyReport.id == report_id))
            if report:
                report.notion_page_id = response["id"]
        return response["id"]
