from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

from pa_digest import cli
from pa_digest.models import Article, PreparedBatch
from pa_digest.state import StateStore


class EmptyMetadataClient:
    def __init__(self, mailto: str):
        self.mailto = mailto

    def discover(self, start, end):
        return []

    def close(self) -> None:
        pass


class NoopSummarizer:
    def summarize(self, article) -> None:
        raise AssertionError("An empty digest must not call the summarizer")


class StubSummarizer:
    def summarize(self, article) -> None:
        article.summary_ko = "초록을 기반으로 생성한 테스트 요약"
        article.summary_basis = "abstract"
        article.topic_area = "조직·인사"
        article.method = "서베이"


def article_with_abstract(abstract: str | None) -> Article:
    from datetime import date

    return Article(
        doi="10.1234/pending",
        title="A Pending Research Article",
        journal="Governance",
        journal_short="Governance",
        publication_date=date(2026, 8, 8),
        url="https://doi.org/10.1234/pending",
        abstract=abstract,
    )


class MissingAbstractMetadataClient(EmptyMetadataClient):
    def discover(self, start, end):
        return [article_with_abstract(None)]


class ResolvedPendingMetadataClient(EmptyMetadataClient):
    def by_public_record(self, record):
        return article_with_abstract("This abstract is now available and contains sufficient detail for the digest.")


def test_prepare_creates_deliverable_batch_when_no_articles(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "build" / "batch.json"
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", EmptyMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", NoopSummarizer)
    args = Namespace(
        state=state_path,
        output=output_path,
        lookback_days=7,
        resend_latest=False,
        dry_run=False,
        daily_once=False,
    )

    assert cli.prepare(args) == 0

    batch = PreparedBatch.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert batch.articles == []
    assert "신규 0편" in batch.subject
    assert "오늘은 새로 확인된 논문이 없습니다." in batch.html
    stored = StateStore(state_path).data["batches"][batch.batch_id]
    assert stored["status"] == "prepared"
    assert stored["items"] == []


def test_daily_once_skips_after_successful_delivery(tmp_path) -> None:
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "build" / "batch.json"
    digest_date = datetime.now(UTC).astimezone(cli.NEW_YORK).date().isoformat()
    store = StateStore(state_path)
    batch_id = f"{digest_date}-existing"
    store.prepare(batch_id, f"key-{batch_id}", [], datetime.now(UTC).isoformat())
    store.mark_sent(batch_id, [], datetime.now(UTC).isoformat())
    store.save()
    args = Namespace(
        state=state_path,
        output=output_path,
        lookback_days=7,
        resend_latest=False,
        dry_run=False,
        daily_once=True,
    )

    assert cli.prepare(args) == 0
    assert not output_path.exists()


def test_prepare_excludes_and_queues_missing_abstract(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "build" / "batch.json"
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", MissingAbstractMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", NoopSummarizer)
    args = Namespace(
        state=state_path,
        output=output_path,
        lookback_days=7,
        resend_latest=False,
        dry_run=False,
        daily_once=False,
    )

    assert cli.prepare(args) == 0
    batch = PreparedBatch.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert batch.articles == []
    assert StateStore(state_path).pending_records == [article_with_abstract(None).public_record()]


def test_pending_article_is_included_once_abstract_appears(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "build" / "batch.json"
    store = StateStore(state_path)
    store.update_pending([article_with_abstract(None)], set(), datetime.now(UTC).isoformat())
    store.save()
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", ResolvedPendingMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", StubSummarizer)
    args = Namespace(
        state=state_path,
        output=output_path,
        lookback_days=7,
        resend_latest=False,
        dry_run=False,
        daily_once=False,
    )

    assert cli.prepare(args) == 0
    batch = PreparedBatch.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert [item.stable_id for item in batch.articles] == [article_with_abstract(None).stable_id]
    assert StateStore(state_path).pending_records == []
