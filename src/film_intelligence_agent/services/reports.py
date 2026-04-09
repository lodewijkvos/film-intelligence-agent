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
                            film_id=film.film_id,
                            section_name=section,
                            rank=rank,
                            item_payload={
                                "title": film.title,
                                "title_url": film.title_url,
                                "status": film.status,
                                "budget": film.budget,
                                "country": film.country,
                                "region": film.region,
                                "production_company": film.production_company,
                                "production_company_url": film.production_company_url,
                                "director": film.director,
                                "director_url": film.director_url,
                                "director_note": film.director_note,
                                "editor": film.editor,
                                "editor_url": film.editor_url,
                                "editor_note": film.editor_note,
                                "composer": film.composer,
                                "composer_url": film.composer_url,
                                "composer_note": film.composer_note,
                                "producers": film.producers,
                                "producer_links": [
                                    {"name": name, "url": url} for name, url in film.producer_links
                                ],
                                "producer_notes": film.producer_notes,
                                "opportunity_score": film.opportunity_score,
                                "why_this_matters": film.why_this_matters,
                                "recent_sources": [
                                    {"name": name, "url": url} for name, url in film.recent_sources
                                ],
                                "source_name": film.source_name,
                                "source_url": film.source_url,
                            },
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
