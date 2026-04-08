from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from jinja2 import Template
from sqlalchemy import desc, select

from film_intel_agent.db.models import Film
from film_intel_agent.db.session import db_session


HTML_TEMPLATE = Template(
    """
    <html>
      <body>
        <h1>Film Intelligence Weekly Report</h1>
        <p>{{ summary }}</p>
        {% for section, films in sections.items() %}
        <h2>{{ section }}</h2>
        <ul>
          {% for film in films %}
          <li>
            <strong>{{ film.title }}</strong><br />
            Budget: {{ film.budget_text or 'Unknown' }}<br />
            Region: {{ film.region or 'Unknown' }}<br />
            Production Company: {{ film.production_company or 'Unknown' }}<br />
            Director: Unknown<br />
            Composer: Unknown<br />
            Producers: Unknown<br />
            Status: {{ film.status or 'Unknown' }}
          </li>
          {% endfor %}
        </ul>
        {% endfor %}
      </body>
    </html>
    """
)


@dataclass(slots=True)
class RenderedReport:
    summary: str
    html: str
    text: str
    sections: dict[str, list[Film]]


class ReportRenderer:
    def render(self) -> RenderedReport:
        with db_session() as session:
            films = list(session.scalars(select(Film).order_by(desc(Film.opportunity_score)).limit(50)))
        sections: dict[str, list[Film]] = defaultdict(list)
        for film in films:
            if film.country == "Canada" and film.status in {"greenlit", "production"}:
                sections["Canada Greenlights"].append(film)
            if film.country == "Canada" and film.source_type in {
                "canada_official_funder",
                "canada_public_funding",
            }:
                sections["Newly Funded Canadian Projects (Early Opportunities)"].append(film)
            if film.genre and "horror" in film.genre.lower():
                sections["Horror < $10M (North America / Europe)"].append(film)
            if film.opportunity_score >= 70:
                sections["Top Opportunities"].append(film)
        summary = (
            f"{len(films)} tracked projects in the current report window. "
            f"{len(sections['Top Opportunities'])} top opportunities flagged."
        )
        text_lines = ["Film Intelligence Weekly Report", "", summary]
        for section_name, items in sections.items():
            text_lines.append("")
            text_lines.append(section_name)
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
        html = HTML_TEMPLATE.render(summary=summary, sections=sections)
        return RenderedReport(summary=summary, html=html, text="\n".join(text_lines), sections=sections)
