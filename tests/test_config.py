from pa_digest.config import FIELDS, JOURNAL_FIELD, JOURNAL_RANK, JOURNAL_TIER, JOURNALS


def test_journal_tiers_follow_sjr_2025() -> None:
    expected_tiers = {
        "Public Administration Review": 1,
        "Journal of Public Administration Research and Theory": 1,
        "Public Administration": 2,
        "Public Management Review": 2,
        "Perspectives on Public Management and Governance": 2,
        "Journal of Policy Analysis and Management": 2,
        "Policy Studies Journal": 3,
        "International Public Management Journal": 3,
        "Public Performance & Management Review": 3,
        "Administration & Society": 3,
        "Journal of Behavioral Public Administration": 3,
        "American Journal of Political Science": 1,
        "American Political Science Review": 1,
        "Political Analysis": 1,
        "The Journal of Politics": 2,
        "Political Behavior": 2,
        "Academy of Management Annals": 1,
        "Academy of Management Review": 1,
        "Journal of Management": 2,
        "Journal of Applied Psychology": 2,
        "Psychological Bulletin": 1,
        "Journal of Personality and Social Psychology": 2,
        "MIS Quarterly": 1,
        "Nature": 1,
        "Proceedings of the National Academy of Sciences": 2,
    }
    for journal, tier in expected_tiers.items():
        assert JOURNAL_TIER[journal] == tier


def test_journals_are_ordered_by_field_then_tier() -> None:
    order = [(FIELDS.index(JOURNAL_FIELD[j.name]), j.tier) for j in JOURNALS]
    assert order == sorted(order)
    assert JOURNAL_RANK["Public Administration Review"] < JOURNAL_RANK["Public Management Review"]
    assert JOURNAL_RANK["Political Analysis"] < JOURNAL_RANK["The Journal of Politics"]


def test_journal_catalog_has_unique_valid_issns() -> None:
    assert len(JOURNALS) == 47
    issns = [issn for journal in JOURNALS for issn in journal.issns]
    assert len(issns) == len(set(issns))
    assert all(len(issn) == 9 and issn[4] == "-" for issn in issns)
