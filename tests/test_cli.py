from argparse import Namespace
from pathlib import Path

from pa_digest import cli
from pa_digest.models import PreparedBatch
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
    )

    assert cli.prepare(args) == 0

    batch = PreparedBatch.model_validate_json(output_path.read_text(encoding="utf-8"))
    assert batch.articles == []
    assert "신규 0편" in batch.subject
    assert "오늘은 새로 확인된 논문이 없습니다." in batch.html
    stored = StateStore(state_path).data["batches"][batch.batch_id]
    assert stored["status"] == "prepared"
    assert stored["items"] == []
