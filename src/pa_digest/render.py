from __future__ import annotations

from collections import OrderedDict
from datetime import date
from html import escape

from .config import JOURNAL_RANK, JOURNAL_TIER
from .models import Article


def _authors(article: Article) -> str:
    if not article.authors:
        return "Authors unavailable"
    if len(article.authors) <= 4:
        return ", ".join(article.authors)
    return ", ".join(article.authors[:3]) + " et al."


def _affiliations_html(article: Article) -> str:
    rows: list[str] = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        if affiliations:
            rows.append(
                f'<div style="margin:4px 0;text-align:justify"><strong>{escape(author)}</strong> — '
                f'{escape("; ".join(affiliations))}</div>'
            )
    if not rows:
        return '<div style="margin-top:8px;color:#6b7280;font-style:italic">Affiliation information unavailable</div>'
    return "".join(rows)


def _affiliations_text(article: Article) -> str:
    rows = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        if affiliations:
            rows.append(f"{author} — {'; '.join(affiliations)}")
    return "\n".join(rows) if rows else "Affiliation information unavailable"


def render_newsletter(articles: list[Article], digest_date: date) -> tuple[str, str, str]:
    count = len(articles)
    subject = f"[PA Journal Digest] {digest_date.isoformat()} · 신규 {count}편"
    grouped: OrderedDict[str, list[Article]] = OrderedDict()
    for article in sorted(
        articles,
        key=lambda item: (JOURNAL_RANK.get(item.journal, 999), item.title.casefold()),
    ):
        grouped.setdefault(article.journal, []).append(article)

    sections: list[str] = []
    text_sections: list[str] = []
    for journal, journal_articles in grouped.items():
        cards: list[str] = []
        text_cards: list[str] = []
        for article in journal_articles:
            abstract_html = (
                f'<div style="margin-top:18px;padding:18px 20px;background:#f7f8fa;border-radius:10px;'
                f'font-size:17px;line-height:1.8;color:#374151;text-align:justify"><strong style="font-size:18px">English abstract</strong><br>'
                f'{escape(article.abstract)}</div>'
                if article.abstract
                else (
                    '<div style="margin-top:18px;padding:18px 20px;background:#fff7ed;border-radius:10px;'
                    'font-size:17px;line-height:1.7;color:#9a3412;text-align:justify"><strong>Abstract unavailable</strong> — '
                    'The Korean note below is based on the title only.</div>'
                )
            )
            cards.append(
                f'<article style="margin:0 0 24px;padding:26px;border:1px solid #d1d5db;border-radius:12px;'
                f'background:#ffffff;font-family:\'Times New Roman\',Times,serif;font-size:17px;line-height:1.75;'
                f'text-align:justify">'
                f'<div style="font-size:15px;color:#4b5563;margin-bottom:10px;text-align:justify">'
                f'{escape(article.publication_date.isoformat())} · {escape(_authors(article))}</div>'
                f'<h3 style="margin:0 0 16px;font-size:23px;line-height:1.45;color:#111827;text-align:justify">'
                f'<a href="{escape(article.url, quote=True)}" style="color:#173f67;text-decoration:none">'
                f'{escape(article.title)}</a></h3>'
                f'<div style="margin-bottom:18px;padding:14px 16px;background:#fafafa;border:1px solid #e5e7eb;'
                f'border-radius:8px;font-size:15px;line-height:1.65;color:#374151;text-align:justify">'
                f'<strong style="font-size:16px;color:#111827">Authors &amp; affiliations</strong>'
                f'{_affiliations_html(article)}</div>'
                f'<div style="padding:18px 20px;background:#eef6ff;border-left:5px solid #2563eb;'
                f'border-radius:8px;font-size:18px;line-height:1.8;color:#172033;text-align:justify">'
                f'<strong style="font-size:19px">한국어 요약</strong><br>'
                f'{escape(article.summary_ko or "요약을 생성하지 못했습니다.")}</div>'
                f'{abstract_html}'
                f'<div style="margin-top:18px;padding:14px 16px;background:#173f67;border-radius:8px;'
                f'font-size:17px;line-height:1.5;text-align:left;color:#ffffff"><strong>DOI</strong><br>'
                f'<a href="{escape(article.url, quote=True)}" style="color:#ffffff;text-decoration:underline;'
                f'word-break:break-all">{escape("https://doi.org/" + article.doi if article.doi else article.url)}</a></div>'
                f'</article>'
            )
            abstract_text = article.abstract or "Abstract unavailable (Korean note is title-based)."
            text_cards.append(
                f"{article.title}\n{_authors(article)} · {article.publication_date.isoformat()}\n"
                f"Authors & affiliations:\n{_affiliations_text(article)}\n"
                f"한국어 요약: {article.summary_ko}\nEnglish abstract: {abstract_text}\n{article.url}"
            )
        sections.append(
            f'<section style="margin:32px 0"><h2 style="margin:0 0 16px;color:#173f67;font-size:25px;'
            f'line-height:1.4;text-align:justify">'
            f'{escape(journal)} <span style="font-size:14px;color:#6b7280">'
            f'Tier {JOURNAL_TIER.get(journal, 3)} · {len(journal_articles)}편</span>'
            f'</h2>{"".join(cards)}</section>'
        )
        text_sections.append(f"## {journal} ({len(journal_articles)})\n\n" + "\n\n".join(text_cards))

    html_body = f"""<!doctype html>
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  html, body, table, td, a {{ -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  table, td {{ mso-table-lspace:0pt; mso-table-rspace:0pt; }}
  table {{ border-collapse:collapse !important; }}
  @media only screen and (max-width:680px) {{ .digest-shell {{ width:100% !important; }} .digest-pad {{ padding:16px 10px !important; }} }}
</style>
<!--[if mso]><style>body,table,td,a,h1,h2,h3,div,span {{font-family:'Times New Roman',Times,serif !important;}}</style><![endif]-->
</head><body style="width:100%;margin:0;padding:0;background:#f3f4f6;font-family:'Times New Roman',Times,serif;font-size:17px;line-height:1.75;color:#111827;text-align:justify;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden">최근 행정학 탑저널 신규 논문 {count}편</div>
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="width:100%;background:#f3f4f6"><tr><td align="center" class="digest-pad" style="padding:28px 16px">
<!--[if mso]><table role="presentation" width="640" border="0" cellspacing="0" cellpadding="0"><tr><td width="640"><![endif]-->
<div class="digest-shell" style="width:100%;max-width:640px;margin:0 auto;font-family:'Times New Roman',Times,serif">
  <header style="padding:30px;background:#173f67;color:white;border-radius:14px;font-family:'Times New Roman',Times,serif;text-align:left">
    <div style="font-size:15px;letter-spacing:.08em;text-transform:uppercase;opacity:.8">Daily research briefing</div>
    <h1 style="margin:8px 0 4px;font-size:34px;line-height:1.3">PA Journal Digest</h1>
    <div style="font-size:18px;opacity:.9">{escape(digest_date.isoformat())} · 신규 논문 {count}편 · {len(grouped)}개 저널</div>
  </header>
  {''.join(sections)}
  <footer style="padding:22px 4px;color:#4b5563;font-size:15px;line-height:1.7;text-align:justify">
    Crossref와 공개 학술 메타데이터를 기반으로 자동 생성되었습니다. 요약은 원문 초록을 대체하지 않습니다.
  </footer>
</div>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table></body></html>"""
    text_body = (
        f"PA Journal Digest\n{digest_date.isoformat()} · 신규 논문 {count}편\n\n"
        + "\n\n".join(text_sections)
        + "\n\n자동 생성 요약은 원문 초록을 대체하지 않습니다."
    )
    return subject, html_body, text_body
