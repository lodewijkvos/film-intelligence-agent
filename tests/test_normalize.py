from film_intelligence_agent.utils.normalize import normalize_name, normalize_title


def test_normalize_title_removes_prefixes():
    assert normalize_title("The Working Title Example!") == "example"


def test_normalize_name_collapses_whitespace():
    assert normalize_name("Lodewijk   Vos") == "lodewijk vos"
