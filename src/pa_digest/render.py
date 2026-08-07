from __future__ import annotations

from collections import OrderedDict
from datetime import date
from html import escape

from .models import Article


def _authors(article: Article) -> str:
    if not article.authors:
        return "Authors unavailable"
    if len(article.authors) <= 4:
        return ", ".join(article.authors)
    return ", ".join(article.authors[:3]) + " et al."


def render_newsletter(articles: list[Article], digest_date: date) -> tuple[str, str, str]:
    count = len(articles)
    subject = f"[PA Journal Digest] {digest_date.isoformat()} · 신규 {count}편"
    grouped: OrderedDict[str, list[Article]] = OrderedDict()
    for article in sorted(articles, key=lambda item: (item.journal, item.title.casefold())):
        grouped.setdefault(article.journal, []).append(article)

    sections: list[str] = []
    text_sections: list[str] = []
    for journal, journal_articles in grouped.items():
        cards: list[str] = []
        text_cards: list[str] = []
        for article in journal_articles:
            abstract_html = (
                f'<div style="margin-top:14px;padding:12px 14px;background:#f7f8fa;border-radius:8px;'
                f'font-size:13px;line-height:1.55;color:#4b5563"><strong>English abstract</strong><br>'
                f'{escape(article.abstract)}</div>'
                if article.abstract
                else (
                    '<div style="margin-top:14px;padding:12px 14px;background:#fff7ed;border-radius:8px;'
                    'font-size:13px;color:#9a3412"><strong>Abstract unavailable</strong> — '
                    'The Korean note below is based on the title only.</div>'
                )
            )
            cards.append(
                f'<article style="margin:0 0 18px;padding:20px;border:1px solid #e5e7eb;border-radius:12px;'
                f'background:#ffffff">'
                f'<div style="font-size:12px;color:#6b7280;margin-bottom:8px">'
                f'{escape(article.publication_date.isoformat())} · {escape(_authors(article))}</div>'
                f'<h3 style="margin:0 0 12px;font-size:18px;line-height:1.35;color:#111827">'
                f'<a href="{escape(article.url, quote=True)}" style="color:#173f67;text-decoration:none">'
                f'{escape(article.title)}</a></h3>'
                f'<div style="padding:14px 16px;background:#eef6ff;border-left:4px solid #2563eb;'
                f'border-radius:6px;line-height:1.65;color:#172033"><strong>한국어 요약</strong><br>'
                f'{escape(article.summary_ko or "요약을 생성하지 못했습니다.")}</div>'
                f'{abstract_html}'
                f'<div style="margin-top:12px;font-size:12px"><a href="{escape(article.url, quote=True)}" '
                f'style="color:#2563eb">DOI / publisher page →</a></div>'
                f'</article>'
            )
            abstract_text = article.abstract or "Abstract unavailable (Korean note is title-based)."
            text_cards.append(
                f"{article.title}\n{_authors(article)} · {article.publication_date.isoformat()}\n"
                f"한국어 요약: {article.summary_ko}\nEnglish abstract: {abstract_text}\n{article.url}"
            )
        sections.append(
            f'<section style="margin:28px 0"><h2 style="margin:0 0 14px;color:#173f67;font-size:21px">'
            f'{escape(journal)} <span style="font-size:13px;color:#6b7280">({len(journal_articles)})</span>'
            f'</h2>{"".join(cards)}</section>'
        )
        text_sections.append(f"## {journal} ({len(journal_articles)})\n\n" + "\n\n".join(text_cards))

    html_body = f"""<!doctype html>
<html><body style="margin:0;background:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#111827">
<div style="display:none;max-height:0;overflow:hidden">최근 행정학 탑저널 신규 논문 {count}편</div>
<main style="max-width:720px;margin:0 auto;padding:28px 16px">
  <header style="padding:28px;background:#173f67;color:white;border-radius:14px">
    <div style="font-size:13px;letter-spacing:.08em;text-transform:uppercase;opacity:.8">Daily research briefing</div>
    <h1 style="margin:8px 0 4px;font-size:29px">PA Journal Digest</h1>
    <div style="opacity:.88">{escape(digest_date.isoformat())} · 신규 논문 {count}편 · {len(grouped)}개 저널</div>
  </header>
  {''.join(sections)}
  <footer style="padding:20px 4px;color:#6b7280;font-size:12px;line-height:1.5">
    Crossref와 공개 학술 메타데이터를 기반으로 자동 생성되었습니다. 요약은 원문 초록을 대체하지 않습니다.
  </footer>
</main></body></html>"""
    text_body = (
        f"PA Journal Digest\n{digest_date.isoformat()} · 신규 논문 {count}편\n\n"
        + "\n\n".join(text_sections)
        + "\n\n자동 생성 요약은 원문 초록을 대체하지 않습니다."
    )
    return subject, html_body, text_body

