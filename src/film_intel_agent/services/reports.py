from __future__ import annotations

from datetime import date

from film_intel_agent.db.models import ReportItem, WeeklyReport
from film_intel_agent.db.session import db_session
from film_intel_agent.email.send import EmailSender
from film_intel_agent.reports.render import ReportRenderer


class WeeklyReportService:
    def generate_and_optionally_send(self, dry_run: bool = True) -> WeeklyReport:
        renderer = ReportRenderer()
        rendered = renderer.render()
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
            for section_name, films in rendered.sections.items():
                for rank, film in enumerate(films, start=1):
                    session.add(
                        ReportItem(
                            weekly_report_id=report.id,
                            film_id=film.id,
                            section_name=section_name,
                            rank=rank,
                            item_payload={
                                "title": film.title,
                                "budget_text": film.budget_text or "Unknown",
                                "status": film.status or "Unknown",
                            },
                        )
                    )
        if dry_run is False:
            EmailSender().send_report(rendered, dry_run=False)
        return report
