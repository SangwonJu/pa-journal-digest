from pa_digest.config import JOURNAL_RANK, JOURNAL_TIER, JOURNALS


def test_requested_journal_tiers_and_order() -> None:
    expected_tiers = {
        "Journal of Public Administration Research and Theory": 1,
        "Public Administration Review": 1,
        "Perspectives on Public Management and Governance": 1,
        "Journal of Policy Analysis and Management": 1,
        "American Journal of Political Science": 1,
        "American Political Science Review": 1,
        "The Journal of Politics": 1,
        "Political Analysis": 1,
        "International Public Management Journal": 2,
        "International Journal of Public Administration": 2,
        "Political Behavior": 2,
        "Political Psychology": 2,
        "Public Opinion Quarterly": 2,
        "Political Communication": 2,
        "Governance": 3,
        "Administration & Society": 3,
        "Public Performance & Management Review": 3,
    }
    for journal, tier in expected_tiers.items():
        assert JOURNAL_TIER[journal] == tier

    assert JOURNAL_RANK["Perspectives on Public Management and Governance"] < JOURNAL_RANK[
        "American Journal of Political Science"
    ]
    assert JOURNAL_RANK["The Journal of Politics"] < JOURNAL_RANK["Public Management Review"]
    assert JOURNAL_RANK["Journal of Policy Analysis and Management"] < JOURNAL_RANK[
        "American Journal of Political Science"
    ]
    assert JOURNAL_RANK["Political Analysis"] < JOURNAL_RANK["Public Management Review"]


def test_journal_catalog_has_unique_valid_issns() -> None:
    assert len(JOURNALS) == 23
    issns = [issn for journal in JOURNALS for issn in journal.issns]
    assert len(issns) == len(set(issns))
    assert all(len(issn) == 9 and issn[4] == "-" for issn in issns)
