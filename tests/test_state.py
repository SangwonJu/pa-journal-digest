from datetime import UTC, date, datetime, timedelta

import pytest

from pa_digest.models import Article
from pa_digest.state import AmbiguousBatchError, StateStore


def article() -> Article:
    return Article(
        doi="10.1234/example",
        title="An Example Article",
        journal="Governance",
        journal_short="Governance",
        publication_date=date(2026, 8, 5),
        url="https://doi.org/10.1234/example",
    )


def test_prepare_and_mark_sent(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)
    now = datetime(2026, 8, 7, tzinfo=UTC)
    store.prepare("batch", "key", [article()], now.isoformat())
    store.save()

    reloaded = StateStore(path)
    assert reloaded.active_prepared_batch(now)[0] == "batch"
    assert article().stable_id not in reloaded.sent_ids

    reloaded.mark_sent("batch", [article()], now.isoformat())
    reloaded.save()
    final = StateStore(path)
    assert final.is_batch_sent("batch")
    assert article().stable_id in final.sent_ids
    assert final.latest_sent_batch()[0] == "batch"


def test_daily_delivery_ignores_explicit_resends(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)
    now = datetime(2026, 8, 7, tzinfo=UTC)
    resend_id = "2026-08-07-original-resend-20260807T120000Z"
    store.prepare(resend_id, "resend-key", [], now.isoformat())
    store.mark_sent(resend_id, [], now.isoformat())
    assert not store.has_daily_delivery("2026-08-07")

    daily_id = "2026-08-07-daily"
    store.prepare(daily_id, "daily-key", [], now.isoformat())
    store.mark_sent(daily_id, [], now.isoformat())
    assert store.has_daily_delivery("2026-08-07")


def test_stale_prepared_batch_stops_automatic_retry(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)
    now = datetime(2026, 8, 7, tzinfo=UTC)
    store.prepare("batch", "key", [article()], (now - timedelta(hours=24)).isoformat())
    with pytest.raises(AmbiguousBatchError):
        store.active_prepared_batch(now)


def test_pending_articles_survive_until_resolved(tmp_path) -> None:
    path = tmp_path / "state.json"
    store = StateStore(path)
    now = datetime(2026, 8, 7, tzinfo=UTC).isoformat()
    waiting = article()
    assert store.update_pending([waiting], set(), now)
    store.save()

    reloaded = StateStore(path)
    assert reloaded.pending_records == [waiting.public_record()]
    assert reloaded.update_pending([], {waiting.stable_id}, now)
    assert reloaded.pending_records == []
