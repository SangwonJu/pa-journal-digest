from pa_digest.config import JOURNAL_RANK, JOURNAL_TIER


def test_requested_journal_tiers_and_order() -> None:
    assert JOURNAL_TIER["Journal of Public Administration Research and Theory"] == 1
    assert JOURNAL_TIER["Public Administration Review"] == 1
    assert JOURNAL_TIER["Perspectives on Public Management and Governance"] == 1
    assert JOURNAL_TIER["International Public Management Journal"] == 2
    assert JOURNAL_TIER["Governance"] == 3
    assert JOURNAL_TIER["Administration & Society"] == 3
    assert JOURNAL_TIER["Public Performance & Management Review"] == 3
    assert JOURNAL_RANK["Perspectives on Public Management and Governance"] < JOURNAL_RANK[
        "Public Management Review"
    ]
