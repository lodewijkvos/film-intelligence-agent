from __future__ import annotations

from datetime import date

from film_intelligence_agent.db.models import ReportItem, WeeklyReport
from film_intelligence_agent.db.session import db_session
from film_intelligence_agent.email.send import EmailService
from film_intelligence_agent.reports.render import ReportRenderer


class WeeklyReportService:
    def generate(self, dry_run: bool = True) -> WeeklyReport:
        rendered = ReportRenderer().render()
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

    def send(self, dry_run: bool = True) -> None:
        rendered = ReportRenderer().render()
        EmailService().send(rendered, dry_run=dry_run)
