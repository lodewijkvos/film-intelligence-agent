from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from jinja2 import Template
from sqlalchemy import desc, select

from film_intelligence_agent.db.models import Film
from film_intelligence_agent.db.session import db_session


SECTION_ORDER = (
    "Top Opportunities",
    "Newly Funded Canadian Projects (Early Opportunities)",
    "Canada Greenlights",
    "Horror < $10M (North America / Europe)",
    "Collaborator Matches",
    "Needs Review",
    "Weekly Summary",
)

SECTION_EMPTY_STATES = {
    "Top Opportunities": "No high-confidence opportunities made the cut for this run.",
    "Newly Funded Canadian Projects (Early Opportunities)": "No funded Canadian film or series projects were captured in this run.",
    "Canada Greenlights": "No Canadian greenlights or active productions were captured in this run.",
    "Horror < $10M (North America / Europe)": "No horror projects in the target budget/region band were captured in this run.",
    "Collaborator Matches": "No direct collaborator or warm-path matches are available yet.",
    "Needs Review": "No low-confidence items are waiting for review right now.",
    "Weekly Summary": "",
}


@dataclass(slots=True)
class RenderedReport:
    summary: str
    html: str
    text: str
    sections: dict[str, list[Film]]
    stats: dict[str, int]
    lookback_days: int


TEMPLATE = Template(
    """
    <html>
      <body style="margin:0;padding:0;background:#f4f1ea;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1a1a1a;">
        <div style="max-width:900px;margin:0 auto;padding:32px 24px 48px;">
          <div style="background:#ffffff;border:1px solid #e2d8c7;border-radius:20px;padding:32px;">
            <p style="margin:0 0 8px;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#7a6d5b;">Film Intelligence Agent</p>
            <h1 style="margin:0 0 12px;font-size:34px;line-height:1.1;">Weekly Intelligence Report</h1>
            <p style="margin:0 0 20px;font-size:17px;line-height:1.5;color:#4f463b;">{{ summary }}</p>

            <table role="presentation" style="width:100%;border-collapse:collapse;margin:0 0 28px;">
              <tr>
                {% for label, value in stats.items() %}
                <td style="padding:12px 10px;border:1px solid #eadfce;background:#faf7f1;">
                  <div style="font-size:12px;text-transform:uppercase;letter-spacing:0.08em;color:#7a6d5b;">{{ label }}</div>
                  <div style="font-size:22px;font-weight:700;margin-top:4px;">{{ value }}</div>
                </td>
                {% endfor %}
              </tr>
            </table>

            {% for section_name in section_order %}
              <div style="margin:0 0 28px;">
                <h2 style="margin:0 0 10px;font-size:20px;">{{ section_name }}</h2>
                {% if section_name == "Weekly Summary" %}
                  <ul style="margin:0;padding-left:20px;color:#3f382f;line-height:1.6;">
                    <li>Lookback window: {{ lookback_days }} days</li>
                    <li>Total qualified projects mirrored this run: {{ stats["Projects Included"] }}</li>
                    <li>Canadian funded/greenlit projects: {{ stats["Canada Signals"] }}</li>
                    <li>Needs review items: {{ stats["Needs Review"] }}</li>
                  </ul>
                {% elif sections[section_name] %}
                  {% for film in sections[section_name] %}
                    <div style="margin:0 0 14px;padding:14px 16px;border:1px solid #eadfce;border-radius:14px;background:#fcfaf6;">
                      <div style="font-size:18px;font-weight:700;margin-bottom:10px;">
                        {% if film.imdb_url %}
                          <a href="{{ film.imdb_url }}" style="color:#1f4f46;text-decoration:none;">{{ film.title }}</a>
                        {% else %}
                          {{ film.title }}
                        {% endif %}
                      </div>
                      <div style="font-size:14px;line-height:1.7;color:#332d26;">
                        <div><strong>Budget:</strong> {{ film.budget_text or "Unknown" }}</div>
                        <div><strong>Region:</strong> {{ film.region or film.country or "Unknown" }}</div>
                        <div><strong>Production Company:</strong> {{ film.production_company or "Unknown" }}</div>
                        <div><strong>Director:</strong> Unknown</div>
                        <div><strong>Composer:</strong> Unknown</div>
                        <div><strong>Producers:</strong> Unknown</div>
                        <div><strong>Status:</strong> {{ film.status or "Unknown" }}</div>
                        <div><strong>Source:</strong> <a href="{{ film.source_url }}" style="color:#1f4f46;">{{ film.source_name }}</a></div>
                      </div>
                    </div>
                  {% endfor %}
                {% else %}
                  <p style="margin:0;color:#6c6256;line-height:1.6;">{{ empty_states[section_name] }}</p>
                {% endif %}
              </div>
            {% endfor %}
          </div>
        </div>
      </body>
    </html>
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
                    .order_by(desc(Film.opportunity_score), desc(Film.data_confidence_score), desc(Film.last_seen_at))
                    .limit(100)
                )
            )

        sections: dict[str, list[Film]] = {name: [] for name in SECTION_ORDER}
        top_opportunities = [film for film in films if film.opportunity_score >= 40][:8]
        funded_canada = [film for film in films if film.country == "Canada" and film.status == "funded"][:8]
        canada_greenlights = [
            film for film in films if film.country == "Canada" and film.status in {"greenlit", "production"}
        ][:8]
        horror_targets = [
            film
            for film in films
            if film.genre
            and "horror" in film.genre.lower()
            and (film.region in {"Canada", "North America", "Europe"} or film.country in {"Canada", "United States"})
        ][:8]
        collaborator_matches: list[Film] = []
        needs_review = [film for film in films if film.data_confidence_score < 70][:8]

        sections["Top Opportunities"] = top_opportunities
        sections["Newly Funded Canadian Projects (Early Opportunities)"] = funded_canada
        sections["Canada Greenlights"] = canada_greenlights
        sections["Horror < $10M (North America / Europe)"] = horror_targets
        sections["Collaborator Matches"] = collaborator_matches
        sections["Needs Review"] = needs_review
        sections["Weekly Summary"] = []

        stats = {
            "Projects Included": len(films),
            "Top Opportunities": len(top_opportunities),
            "Canada Signals": len({film.id for film in funded_canada + canada_greenlights}),
            "Needs Review": len(needs_review),
        }
        summary = (
            f"{len(films)} qualified film/series projects in the last {lookback_days} days. "
            f"This page mirrors the email structure you’ll receive every Monday at 9:00 a.m. Toronto time."
        )

        text_lines = [
            "Film Intelligence Weekly Report",
            "",
            summary,
            "",
        ]
        for section_name in SECTION_ORDER:
            text_lines.append(section_name)
            if section_name == "Weekly Summary":
                text_lines.extend(
                    [
                        f"- Lookback window: {lookback_days} days",
                        f"- Projects included: {stats['Projects Included']}",
                        f"- Canada signals: {stats['Canada Signals']}",
                        f"- Needs review: {stats['Needs Review']}",
                    ]
                )
            elif sections[section_name]:
                for film in sections[section_name]:
                    text_lines.extend(
                        [
                            f"- {film.title}",
                            f"  Budget: {film.budget_text or 'Unknown'}",
                            f"  Region: {film.region or film.country or 'Unknown'}",
                            f"  Production Company: {film.production_company or 'Unknown'}",
                            "  Director: Unknown",
                            "  Composer: Unknown",
                            "  Producers: Unknown",
                            f"  Status: {film.status or 'Unknown'}",
                            f"  Source: {film.source_name} ({film.source_url})",
                        ]
                    )
            else:
                text_lines.append(f"- {SECTION_EMPTY_STATES[section_name]}")
            text_lines.append("")

        html = TEMPLATE.render(
            summary=summary,
            sections=sections,
            section_order=SECTION_ORDER,
            empty_states=SECTION_EMPTY_STATES,
            stats=stats,
            lookback_days=lookback_days,
        )
        return RenderedReport(
            summary=summary,
            html=html,
            text="\n".join(text_lines).strip(),
            sections=sections,
            stats=stats,
            lookback_days=lookback_days,
        )
