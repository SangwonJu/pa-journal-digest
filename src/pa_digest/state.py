from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from .models import Article


class AmbiguousBatchError(RuntimeError):
    pass


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "articles": {}, "batches": {}}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    @property
    def sent_ids(self) -> set[str]:
        return set(self.data.get("articles", {}))

    def active_prepared_batch(self, now: datetime | None = None) -> tuple[str, dict[str, Any]] | None:
        now = now or datetime.now(UTC)
        prepared = [
            (batch_id, batch)
            for batch_id, batch in self.data.get("batches", {}).items()
            if batch.get("status") == "prepared"
        ]
        if not prepared:
            return None
        prepared.sort(key=lambda item: item[1]["created_at"])
        batch_id, batch = prepared[0]
        created = datetime.fromisoformat(batch["created_at"])
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        if now - created >= timedelta(hours=24):
            raise AmbiguousBatchError(
                f"Batch {batch_id} has been prepared for 24 hours or more. "
                "Check Resend before retrying to avoid a duplicate email."
            )
        return batch_id, batch

    def prepare(self, batch_id: str, idempotency_key: str, articles: list[Article], created_at: str) -> None:
        self.data.setdefault("batches", {})[batch_id] = {
            "status": "prepared",
            "created_at": created_at,
            "idempotency_key": idempotency_key,
            "items": [article.public_record() for article in articles],
        }

    def mark_sent(self, batch_id: str, articles: list[Article], sent_at: str) -> None:
        batch = self.data["batches"][batch_id]
        if batch.get("status") == "sent":
            return
        batch["status"] = "sent"
        batch["sent_at"] = sent_at
        for article in articles:
            self.data.setdefault("articles", {})[article.stable_id] = {
                "batch_id": batch_id,
                "sent_at": sent_at,
                "doi": normalize_nullable(article.doi),
                "title": article.title,
                "journal": article.journal,
                "publication_date": article.publication_date.isoformat(),
            }

    def is_batch_sent(self, batch_id: str) -> bool:
        return self.data.get("batches", {}).get(batch_id, {}).get("status") == "sent"


def normalize_nullable(value: str | None) -> str | None:
    from .models import normalize_doi

    return normalize_doi(value)

