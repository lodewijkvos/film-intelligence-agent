from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from jinja2 import Template
from sqlalchemy import desc, select

from film_intelligence_agent.db.models import Film
from film_intelligence_agent.db.session import db_session


@dataclass(slots=True)
class RenderedReport:
    summary: str
    html: str
    text: str
    sections: dict[str, list[Film]]


TEMPLATE = Template(
    """
    <html><body>
    <h1>Film Intelligence Weekly Report</h1>
    <p>{{ summary }}</p>
    {% for section, films in sections.items() %}
    <h2>{{ section }}</h2>
    <ul>
    {% for film in films %}
      <li>
        <strong>{{ film.title }}</strong><br/>
        Budget: {{ film.budget_text or "Unknown" }}<br/>
        Region: {{ film.region or "Unknown" }}<br/>
        Production Company: {{ film.production_company or "Unknown" }}<br/>
        Director: Unknown<br/>
        Composer: Unknown<br/>
        Producers: Unknown<br/>
        Status: {{ film.status or "Unknown" }}
      </li>
    {% endfor %}
    </ul>
    {% endfor %}
    </body></html>
    """
)


class ReportRenderer:
    def render(self, lookback_days: int = 14) -> RenderedReport:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        with db_session() as session:
            films = list(
                session.scalars(
                    select(Film)
                    .where(Film.first_seen_at >= cutoff)
                    .order_by(desc(Film.opportunity_score))
                    .limit(50)
                )
            )
        sections: dict[str, list[Film]] = defaultdict(list)
        for film in films:
            if film.opportunity_score >= 40:
                sections["Top Opportunities"].append(film)
            if film.country == "Canada" and film.status == "funded":
                sections["Newly Funded Canadian Projects (Early Opportunities)"].append(film)
            if film.country == "Canada" and film.status in {"greenlit", "production"}:
                sections["Canada Greenlights"].append(film)
            if film.genre and "horror" in film.genre.lower():
                sections["Horror < $10M (North America / Europe)"].append(film)
            if film.data_confidence_score < 70:
                sections["Needs Review"].append(film)
        summary = f"{len(films)} tracked projects in the last {lookback_days} days."
        text_lines = ["Film Intelligence Weekly Report", "", summary]
        for section, items in sections.items():
            text_lines.append("")
            text_lines.append(section)
            for film in items:
                text_lines.extend(
                    [
                        f"- {film.title}",
                        f"  Budget: {film.budget_text or 'Unknown'}",
                        f"  Region: {film.region or 'Unknown'}",
                        f"  Production Company: {film.production_company or 'Unknown'}",
                        "  Director: Unknown",
                        "  Composer: Unknown",
                        "  Producers: Unknown",
                        f"  Status: {film.status or 'Unknown'}",
                    ]
                )
        return RenderedReport(summary=summary, html=TEMPLATE.render(summary=summary, sections=sections), text="\n".join(text_lines), sections=sections)
