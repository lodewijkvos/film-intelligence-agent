from film_intelligence_agent.reports.render import TEMPLATE


def test_report_template_contains_required_labels():
    html = TEMPLATE.render(summary="Summary", sections={})
    assert "Film Intelligence Weekly Report" in html
