from __future__ import annotations

from datetime import date
from datetime import datetime, timedelta

from sqlalchemy import func, select

from film_intelligence_agent.db.models import Film
from film_intelligence_agent.db.models import ReportItem, WeeklyReport
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.email.send import EmailService
from film_intelligence_agent.reports.render import ReportRenderer


class WeeklyReportService:
    def generate(self, dry_run: bool = True, lookback_days: int = 14) -> WeeklyReport:
        rendered = ReportRenderer().render(lookback_days=lookback_days)
        with db_session() as session:
            report = WeeklyReport(
                report_date=date.today(),
                dry_run=dry_run,
                summary_text=rendered.summary,
                report_html=rendered.html,
                report_text=rendered.text,
                status="generated",
            )
            session.add(report)
            session.flush()
            for section, items in rendered.sections.items():
                for rank, film in enumerate(items, start=1):
                    session.add(
                        ReportItem(
                            weekly_report_id=report.id,
                            film_id=film.id,
                            section_name=section,
                            rank=rank,
                            item_payload={"title": film.title, "status": film.status, "budget": film.budget_text},
                        )
                    )
        return report

    def send(self, dry_run: bool = True, lookback_days: int = 14) -> None:
        rendered = ReportRenderer().render(lookback_days=lookback_days)
        EmailService().send(rendered, dry_run=dry_run)

    def choose_lookback_days(self) -> int:
        recent_cutoff = datetime.utcnow() - timedelta(days=14)
        with db_session() as session:
            recent_count = session.scalar(select(func.count()).select_from(Film).where(Film.first_seen_at >= recent_cutoff)) or 0
        return 180 if recent_count == 0 else 14
