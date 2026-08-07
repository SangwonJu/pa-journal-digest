from __future__ import annotations

import hashlib
import re
from datetime import date

from pydantic import BaseModel, Field, computed_field


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    doi = value.strip().lower()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi)
    return doi.rstrip(". ") or None


def fallback_article_id(journal: str, title: str, publication_date: date) -> str:
    normalized_title = " ".join(title.casefold().split())
    raw = f"{journal.casefold()}|{normalized_title}|{publication_date.isoformat()}"
    return "hash:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


class Article(BaseModel):
    doi: str | None = None
    title: str
    journal: str
    journal_short: str
    authors: list[str] = Field(default_factory=list)
    publication_date: date
    url: str
    abstract: str | None = None
    abstract_source: str | None = None
    summary_ko: str | None = None
    summary_basis: str | None = None

    @computed_field
    @property
    def stable_id(self) -> str:
        doi = normalize_doi(self.doi)
        return f"doi:{doi}" if doi else fallback_article_id(self.journal, self.title, self.publication_date)

    def public_record(self) -> dict[str, object]:
        return {
            "stable_id": self.stable_id,
            "doi": normalize_doi(self.doi),
            "title": self.title,
            "journal": self.journal,
            "journal_short": self.journal_short,
            "authors": self.authors,
            "publication_date": self.publication_date.isoformat(),
            "url": self.url,
        }


class PreparedBatch(BaseModel):
    batch_id: str
    idempotency_key: str
    created_at: str
    articles: list[Article]
    subject: str
    html: str
    text: str

