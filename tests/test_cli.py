from argparse import Namespace
from datetime import UTC, datetime
from pathlib import Path

from pa_digest import cli
from pa_digest.models import Article, PreparedBatch
from pa_digest.state import StateStore


class EmptyMetadataClient:
    def __init__(self, mailto: str):
        self.mailto = mailto

    def discover(self, start, end, relevance_filter=None):
        return []

    def close(self) -> None:
        pass


class NoopSummarizer:
    def select_ai_social(self, articles):
        return articles

    def summarize(self, article) -> None:
        raise AssertionError("An empty digest must not call the summarizer")


class StubSummarizer:
    def select_ai_social(self, articles):
        return articles

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
    def discover(self, start, end, relevance_filter=None):
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


class EditorialSummarizer(StubSummarizer):
    def summarize(self, article) -> None:
        super().summarize(article)
        article.is_editorial = True


class EditorialMetadataClient(EmptyMetadataClient):
    def discover(self, start, end, relevance_filter=None):
        return [article_with_abstract("An introduction from the guest editors that previews each paper.")]


def test_editorials_are_dropped_and_not_summarized_again(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "state.json"
    output_path = tmp_path / "build" / "batch.json"
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", EditorialMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", EditorialSummarizer)
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
    assert article_with_abstract(None).stable_id in StateStore(state_path).skipped_ids

    monkeypatch.setattr(cli, "ArticleSummarizer", NoopSummarizer)
    state = StateStore(state_path)
    state.data["batches"] = {}
    state.save()
    assert cli.prepare(args) == 0


def pnas_article(title: str) -> Article:
    from datetime import date

    return Article(
        doi=f"10.1073/{title.replace(' ', '-')}",
        title=title,
        journal="Proceedings of the National Academy of Sciences",
        journal_short="PNAS",
        publication_date=date(2026, 8, 8),
        url="https://example.test",
        abstract="A sufficiently long abstract for the test.",
    )


class MixedPnasMetadataClient(EmptyMetadataClient):
    def discover(self, start, end, relevance_filter=None):
        return [pnas_article("LLM persuasion"), pnas_article("Sleep loss and phishing")]


class AiJudgingSummarizer(StubSummarizer):
    def summarize(self, article) -> None:
        super().summarize(article)
        article.ai_related = article.title.startswith("LLM")


def _prepare_args(tmp_path, **overrides) -> Namespace:
    values = dict(
        state=tmp_path / "state.json",
        output=tmp_path / "build" / "batch.json",
        lookback_days=7,
        resend_latest=False,
        dry_run=False,
        daily_once=False,
    )
    values.update(overrides)
    return Namespace(**values)


def test_ai_only_journal_needs_per_paper_ai_confirmation(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", MixedPnasMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", AiJudgingSummarizer)
    args = _prepare_args(tmp_path)

    assert cli.prepare(args) == 0
    batch = PreparedBatch.model_validate_json(args.output.read_text(encoding="utf-8"))
    assert [item.title for item in batch.articles] == ["LLM persuasion"]
    assert pnas_article("Sleep loss and phishing").stable_id in StateStore(args.state).skipped_ids


def test_include_sent_rebuilds_papers_already_delivered(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", MixedPnasMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", AiJudgingSummarizer)
    store = StateStore(tmp_path / "state.json")
    store.prepare("old", "key", [pnas_article("LLM persuasion")], datetime.now(UTC).isoformat())
    store.mark_sent("old", [pnas_article("LLM persuasion")], datetime.now(UTC).isoformat())
    store.save()

    args = _prepare_args(tmp_path, include_sent=True)
    assert cli.prepare(args) == 0
    batch = PreparedBatch.model_validate_json(args.output.read_text(encoding="utf-8"))
    assert [item.title for item in batch.articles] == ["LLM persuasion"]
    assert "-resend-recent-" in batch.batch_id
    assert "재발송" in batch.subject


def polbeh_article(title: str) -> Article:
    from datetime import date

    return Article(
        doi=f"10.1007/{title.replace(' ', '-')}",
        title=title,
        journal="Political Behavior",
        journal_short="PolBeh",
        publication_date=date(2026, 8, 8),
        url="https://example.test",
        abstract="A sufficiently long abstract for the test.",
    )


class MixedPolBehMetadataClient(EmptyMetadataClient):
    def discover(self, start, end, relevance_filter=None):
        return [
            polbeh_article("LLM persuasion"),
            polbeh_article("Bureaucrats and citizen trust"),
            polbeh_article("Campaign ads and turnout"),
        ]


class AiOrPaJudgingSummarizer(StubSummarizer):
    def summarize(self, article) -> None:
        super().summarize(article)
        article.ai_related = article.title.startswith("LLM")
        article.pa_related = article.title.startswith("Bureaucrats")


def test_ai_or_pa_journal_keeps_ai_and_public_administration_papers(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("CROSSREF_MAILTO", "researcher@example.edu")
    monkeypatch.setattr(cli, "MetadataClient", MixedPolBehMetadataClient)
    monkeypatch.setattr(cli, "ArticleSummarizer", AiOrPaJudgingSummarizer)
    args = _prepare_args(tmp_path)

    assert cli.prepare(args) == 0
    batch = PreparedBatch.model_validate_json(args.output.read_text(encoding="utf-8"))
    assert sorted(item.title for item in batch.articles) == ["Bureaucrats and citizen trust", "LLM persuasion"]
    assert polbeh_article("Campaign ads and turnout").stable_id in StateStore(args.state).skipped_ids
