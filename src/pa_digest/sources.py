from __future__ import annotations

import html
import os
import re
import time
from datetime import date
from typing import Any
from urllib.parse import quote

import httpx

from .config import JOURNAL_BY_NAME, JOURNALS, Journal
from .models import Article, normalize_doi


CROSSREF_API = "https://api.crossref.org"
SEMANTIC_SCHOLAR_API = "https://api.semanticscholar.org/graph/v1"
OPENALEX_API = "https://api.openalex.org"

EXCLUDED_TITLE_PATTERNS = (
    r"^book review(?::|$)",
    r"^review of\s+.+\bby\b",
    r"^(correction|corrigendum|erratum|retraction)(?::|\s|$)",
    r"^(editorial|editor['’]s introduction|introduction to the (special )?issue)(?::|\s|$)",
    r"^(contents|table of contents|front matter|back matter)$",
    r"^obituary(?::|\s|$)",
    r"\bisbn\b",
    r"\b\d+\s*pp\.\s*(?:[$£€]|\()",
    r"\((?:hardcover|paperback|cloth|ebook)\)",
)


def clean_markup(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    text = html.unescape(text)
    text = " ".join(text.split())
    return text or None


def is_scholarly_article(title: str) -> bool:
    normalized = " ".join(title.split()).strip()
    return not any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in EXCLUDED_TITLE_PATTERNS)


def _date_parts(message: dict[str, Any], field: str) -> date | None:
    parts = message.get(field, {}).get("date-parts", [])
    if not parts or not parts[0]:
        return None
    values = list(parts[0]) + [1, 1]
    try:
        return date(int(values[0]), int(values[1]), int(values[2]))
    except (TypeError, ValueError):
        return None


def publication_date(message: dict[str, Any]) -> date | None:
    for field in ("published-online", "published", "issued", "published-print"):
        parsed = _date_parts(message, field)
        if parsed:
            return parsed
    return None


def author_details(message: dict[str, Any]) -> tuple[list[str], dict[str, list[str]]]:
    names: list[str] = []
    affiliations: dict[str, list[str]] = {}
    for author in message.get("author", []):
        name = " ".join(filter(None, [author.get("given"), author.get("family")])).strip()
        if name:
            names.append(name)
            institutions = [
                " ".join(str(item.get("name", "")).split())
                for item in author.get("affiliation", [])
                if item.get("name")
            ]
            if institutions:
                affiliations[name] = list(dict.fromkeys(institutions))
    return names, affiliations


class MetadataClient:
    def __init__(self, mailto: str, timeout: float = 25.0):
        self.mailto = mailto
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": f"pa-journal-digest/0.1 (mailto:{mailto})"},
        )

    def close(self) -> None:
        self.client.close()

    def _get(self, url: str, *, params: dict[str, str] | None = None) -> httpx.Response:
        for attempt in range(4):
            response = self.client.get(url, params=params)
            if response.status_code not in {429, 500, 502, 503, 504}:
                response.raise_for_status()
                return response
            if attempt == 3:
                response.raise_for_status()
            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after and retry_after.isdigit() else 2**attempt
            time.sleep(min(delay, 8))
        raise RuntimeError("unreachable")

    def discover(self, start: date, end: date) -> list[Article]:
        found: dict[str, Article] = {}
        for journal in JOURNALS:
            for article in self._crossref_journal(journal, start, end):
                found.setdefault(article.stable_id, article)
        articles = sorted(found.values(), key=lambda item: (item.journal, item.publication_date, item.title))
        for article in articles:
            if article.doi and (
                not article.abstract
                or any(author not in article.author_affiliations for author in article.authors)
            ):
                self.enrich_metadata(article)
        return articles

    def _crossref_journal(self, journal: Journal, start: date, end: date) -> list[Article]:
        response = self._get(
            f"{CROSSREF_API}/journals/{journal.primary_issn}/works",
            params={
                "filter": (
                    f"from-pub-date:{start.isoformat()},until-pub-date:{end.isoformat()},"
                    "type:journal-article"
                ),
                "rows": "100",
                "mailto": self.mailto,
                "select": (
                    "DOI,title,author,published-online,published,published-print,issued,URL,abstract,"
                    "container-title,type"
                ),
            },
        )
        items = response.json()["message"].get("items", [])
        parsed: list[Article] = []
        for item in items:
            article = self._article_from_crossref(item, expected_journal=journal)
            if article and start <= article.publication_date <= end and is_scholarly_article(article.title):
                parsed.append(article)
        return parsed

    def by_public_record(self, record: dict[str, Any]) -> Article:
        doi = normalize_doi(record.get("doi"))
        if doi:
            try:
                response = self._get(
                    f"{CROSSREF_API}/works/{quote(doi, safe='')}",
                    params={"mailto": self.mailto},
                )
                journal = JOURNAL_BY_NAME.get(str(record["journal"]))
                article = self._article_from_crossref(response.json()["message"], expected_journal=journal)
                if article:
                    if not article.abstract or any(
                        author not in article.author_affiliations for author in article.authors
                    ):
                        self.enrich_metadata(article)
                    return article
            except (httpx.HTTPError, KeyError, ValueError):
                pass
        article = Article.model_validate(record)
        if article.doi and (
            not article.abstract
            or any(author not in article.author_affiliations for author in article.authors)
        ):
            self.enrich_metadata(article)
        return article

    def _article_from_crossref(
        self, item: dict[str, Any], expected_journal: Journal | None
    ) -> Article | None:
        titles = item.get("title") or []
        pub_date = publication_date(item)
        if not titles or not pub_date:
            return None
        journal = expected_journal
        if journal is None:
            container = (item.get("container-title") or [""])[0]
            journal = JOURNAL_BY_NAME.get(container)
        if journal is None:
            return None
        doi = normalize_doi(item.get("DOI"))
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        authors, author_affiliations = author_details(item)
        return Article(
            doi=doi,
            title=clean_markup(str(titles[0])) or str(titles[0]),
            journal=journal.name,
            journal_short=journal.short_name,
            authors=authors,
            author_affiliations=author_affiliations,
            publication_date=pub_date,
            url=url,
            abstract=clean_markup(item.get("abstract")),
            abstract_source="Crossref" if item.get("abstract") else None,
        )

    def enrich_metadata(self, article: Article) -> None:
        if not article.doi:
            return
        abstract = self._semantic_scholar_abstract(article.doi) if not article.abstract else None
        if abstract:
            article.abstract = clean_markup(abstract)
            article.abstract_source = "Semantic Scholar"
        if not article.abstract or any(
            author not in article.author_affiliations for author in article.authors
        ):
            self._apply_openalex_metadata(article)

    def _semantic_scholar_abstract(self, doi: str) -> str | None:
        try:
            response = self._get(
                f"{SEMANTIC_SCHOLAR_API}/paper/DOI:{quote(doi, safe='')}",
                params={"fields": "abstract"},
            )
            return response.json().get("abstract")
        except (httpx.HTTPError, KeyError, ValueError):
            return None

    def _apply_openalex_metadata(self, article: Article) -> None:
        if not article.doi:
            return
        params = {"select": "abstract_inverted_index,authorships"}
        api_key = os.getenv("OPENALEX_API_KEY")
        if api_key:
            params["api_key"] = api_key
        try:
            response = self._get(
                f"{OPENALEX_API}/works/doi:{quote(article.doi, safe='')}", params=params
            )
            payload = response.json()
            if not article.abstract:
                abstract = abstract_from_inverted_index(payload.get("abstract_inverted_index"))
                if abstract:
                    article.abstract = abstract
                    article.abstract_source = "OpenAlex"
            apply_openalex_affiliations(article, payload.get("authorships") or [])
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            return


def abstract_from_inverted_index(inverted: dict[str, list[int]] | None) -> str | None:
    if not inverted:
        return None
    positioned = sorted(
        ((position, word) for word, positions in inverted.items() for position in positions),
        key=lambda item: item[0],
    )
    return " ".join(word for _, word in positioned)


def _normalized_person_name(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def apply_openalex_affiliations(article: Article, authorships: list[dict[str, Any]]) -> None:
    exact = {_normalized_person_name(author): author for author in article.authors}
    by_family: dict[str, list[str]] = {}
    for author in article.authors:
        family = _normalized_person_name(author.split()[-1])
        by_family.setdefault(family, []).append(author)
    for authorship in authorships:
        openalex_name = str(authorship.get("author", {}).get("display_name", "")).strip()
        if not openalex_name:
            continue
        matched = exact.get(_normalized_person_name(openalex_name))
        if not matched:
            candidates = by_family.get(_normalized_person_name(openalex_name.split()[-1]), [])
            matched = candidates[0] if len(candidates) == 1 else None
        if not matched or article.author_affiliations.get(matched):
            continue
        institutions = [
            " ".join(str(institution.get("display_name", "")).split())
            for institution in authorship.get("institutions", [])
            if institution.get("display_name")
        ]
        if institutions:
            article.author_affiliations[matched] = list(dict.fromkeys(institutions))
