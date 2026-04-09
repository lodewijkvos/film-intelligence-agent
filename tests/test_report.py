from film_intelligence_agent.reports.render import SECTION_ORDER, TEMPLATE


def test_report_template_contains_required_labels():
    html = TEMPLATE.render(
        summary="Summary",
        sections={section: [] for section in SECTION_ORDER},
        section_order=SECTION_ORDER,
        empty_states={section: "" for section in SECTION_ORDER},
        stats={"Projects Included": 0, "Top Opportunities": 0, "Canada Signals": 0, "Needs Review": 0},
        lookback_days=14,
    )
    assert "Film Intelligence Weekly Report" in html
    assert "Top Opportunities" in html
    assert "Weekly Summary" in html
