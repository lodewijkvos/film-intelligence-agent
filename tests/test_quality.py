from film_intelligence_agent.utils.quality import is_probable_project_title


def test_project_title_filter_rejects_navigation_labels() -> None:
    assert not is_probable_project_title("Location Library")
    assert not is_probable_project_title("Production Equipment + Suppliers")
    assert not is_probable_project_title("BC Film Commission")
    assert not is_probable_project_title("Reports")
    assert not is_probable_project_title("Overview")
    assert not is_probable_project_title("Follow Ontario Creates")


def test_project_title_filter_accepts_normal_project_titles() -> None:
    assert is_probable_project_title("Dark Harvest")
    assert is_probable_project_title("The Silent Shore")
