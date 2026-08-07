from __future__ import annotations

from collections import OrderedDict
from datetime import date
from html import escape, unescape

from .config import JOURNAL_RANK, JOURNAL_TIER
from .models import Article


FONT_STACK = "'Times New Roman', Times, serif"


def _affiliations_html(article: Article) -> str:
    if not article.authors:
        return '<div style="margin-top:5px;color:#737373;font-style:italic">Authors unavailable</div>'
    rows: list[str] = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        if affiliations:
            rows.append(
                f'<div style="margin:3px 0;text-align:left"><strong>{escape(author)}</strong> — '
                f'{escape(unescape("; ".join(affiliations)))}</div>'
            )
        else:
            rows.append(
                f'<div style="margin:3px 0;text-align:left"><strong>{escape(author)}</strong> — '
                '<span style="color:#737373;font-style:italic">Affiliation unavailable</span></div>'
            )
    return "".join(rows)


def _affiliations_text(article: Article) -> str:
    if not article.authors:
        return "Authors unavailable"
    rows = []
    for author in article.authors:
        affiliations = article.author_affiliations.get(author, [])
        if affiliations:
            rows.append(f"{author} — {unescape('; '.join(affiliations))}")
        else:
            rows.append(f"{author} — Affiliation unavailable")
    return "\n".join(rows)


def _tags_html(article: Article) -> str:
    method = article.method or "방법 미상"
    if article.method_detail and method != "방법 미상":
        method = f"{method} ({article.method_detail})"
    tags = [
        (article.topic_area or "분야 미상", "#f5eee3", "#795b2f", "#d9c39e"),
        (method, "#eaf1f4", "#315b70", "#b8cbd4"),
    ]
    tags.extend((construct, "#f1eff5", "#574a6d", "#cbc3d8") for construct in article.constructs[:2])
    cells = "".join(
        '<td valign="top" style="padding:0 5px 6px 0">'
        '<table role="presentation" border="0" cellspacing="0" cellpadding="0"><tr>'
        f'<td style="padding:5px 8px;border:1px solid {border};background:{background};'
        f'font-family:{FONT_STACK};font-size:12px;line-height:1.2;color:{color};text-align:left;'
        f'white-space:nowrap"><strong>{escape(value)}</strong></td>'
        '</tr></table></td>'
        for value, background, color, border in tags
    )
    return (
        '<table role="presentation" border="0" cellspacing="0" cellpadding="0" '
        f'style="margin:0 0 2px;font-family:{FONT_STACK}"><tr>{cells}</tr></table>'
    )


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
    article_number = 0
    for journal, journal_articles in grouped.items():
        entries: list[str] = []
        text_entries: list[str] = []
        for article in journal_articles:
            article_number += 1
            number = f"{article_number:02d}"
            abstract_html = (
                f'<div style="margin-top:20px;font-family:{FONT_STACK};font-size:16px;line-height:1.65;'
                f'color:#343434;text-align:left"><div style="margin-bottom:7px;font-size:12px;'
                f'line-height:1.2;letter-spacing:1.2px;color:#6b7280;text-transform:uppercase;'
                f'font-weight:bold">Abstract</div>{escape(article.abstract)}</div>'
                if article.abstract
                else (
                    f'<div style="margin-top:20px;padding:12px 14px;background:#fff8ed;'
                    f'border-left:3px solid #b7791f;font-family:{FONT_STACK};font-size:15px;'
                    'line-height:1.6;color:#714b12;text-align:left"><strong>Abstract unavailable.</strong> '
                    'The Korean note below is based on the title only.</div>'
                )
            )
            doi_url = "https://doi.org/" + article.doi if article.doi else article.url
            entries.append(
                '<tr><td style="padding:27px 0 29px;border-bottom:1px solid #d9d6cf;'
                f'font-family:{FONT_STACK};text-align:left">'
                '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">'
                '<tr>'
                f'<td width="42" valign="top" style="width:42px;padding:3px 10px 0 0;font-family:{FONT_STACK};'
                f'font-size:14px;line-height:1;color:#9a7b45;text-align:left">{number}</td>'
                f'<td valign="top" style="font-family:{FONT_STACK};text-align:left">'
                f'<div style="margin:0 0 7px;font-family:{FONT_STACK};font-size:13px;line-height:1.4;'
                f'color:#74706a;text-align:left">{escape(article.publication_date.isoformat())}</div>'
                f'{_tags_html(article)}'
                f'<h3 style="margin:0 0 13px;font-family:{FONT_STACK};font-size:21px;line-height:1.32;'
                f'font-weight:bold;color:#172c42;text-align:left"><a href="{escape(article.url, quote=True)}" '
                f'style="color:#172c42;text-decoration:none">{escape(article.title)}</a></h3>'
                f'<div style="margin:0 0 19px;font-family:{FONT_STACK};font-size:14px;line-height:1.55;'
                f'color:#55514b;text-align:left"><div style="margin-bottom:5px;font-size:12px;line-height:1.2;'
                f'letter-spacing:1.1px;color:#6b7280;text-transform:uppercase;font-weight:bold">'
                f'Authors &amp; affiliations</div>{_affiliations_html(article)}</div>'
                f'<div style="padding:13px 15px;background:#f3f6f7;border-left:3px solid #315b70;'
                f'font-family:{FONT_STACK};font-size:15px;line-height:1.65;color:#202d34;text-align:left">'
                f'<div style="margin-bottom:5px;font-size:13px;line-height:1.25;font-weight:bold;color:#315b70">'
                f'한국어 요약</div>{escape(article.summary_ko or "요약을 생성하지 못했습니다.")}</div>'
                f'{abstract_html}'
                f'<div style="margin-top:19px;padding-top:10px;border-top:1px dotted #c9c5bd;'
                f'font-family:{FONT_STACK};font-size:13px;line-height:1.5;color:#5f5a53;text-align:left">'
                f'<strong style="color:#172c42">DOI</strong>&nbsp;&nbsp;'
                f'<a href="{escape(article.url, quote=True)}" style="color:#315b70;text-decoration:underline;'
                f'word-break:break-all">{escape(doi_url)}</a></div>'
                '</td></tr></table></td></tr>'
            )
            abstract_text = article.abstract or "Abstract unavailable (Korean note is title-based)."
            text_entries.append(
                f"{number}. {article.title}\n{article.publication_date.isoformat()}\n"
                f"[{article.topic_area or '분야 미상'}] "
                f"[{article.method or '방법 미상'}"
                f"{f' ({article.method_detail})' if article.method_detail else ''}] "
                f"{' '.join(f'[{construct}]' for construct in article.constructs)}\n"
                f"Authors & affiliations:\n{_affiliations_text(article)}\n"
                f"한국어 요약: {article.summary_ko}\nEnglish abstract: {abstract_text}\n{doi_url}"
            )
        sections.append(
            '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" '
            f'style="width:100%;font-family:{FONT_STACK}">'
            '<tr><td style="padding:34px 0 0;font-family:'
            f'{FONT_STACK};text-align:left">'
            '<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0">'
            '<tr>'
            f'<td valign="bottom" style="padding:0 0 10px;border-bottom:2px solid #172c42;font-family:{FONT_STACK};'
            f'font-size:22px;line-height:1.25;font-weight:bold;color:#172c42;text-align:left">{escape(journal)}</td>'
            f'<td width="82" valign="bottom" style="width:82px;padding:0 0 11px;border-bottom:2px solid #172c42;'
            f'font-family:{FONT_STACK};font-size:12px;line-height:1.2;letter-spacing:.6px;color:#74706a;'
            f'text-align:right">TIER {JOURNAL_TIER.get(journal, 3)} · {len(journal_articles)}편</td>'
            f'</tr></table></td></tr>{"".join(entries)}</table>'
        )
        text_sections.append(f"## {journal} ({len(journal_articles)})\n\n" + "\n\n".join(text_entries))

    html_body = f"""<!doctype html>
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  html, body, table, td, a {{ -webkit-text-size-adjust:100%; -ms-text-size-adjust:100%; }}
  table, td {{ mso-table-lspace:0pt; mso-table-rspace:0pt; }}
  table {{ border-collapse:collapse !important; }}
  @media only screen and (max-width:940px) {{ .digest-shell {{ width:100% !important; }} .digest-pad {{ padding:12px 8px !important; }} .content-pad {{ padding-left:20px !important; padding-right:20px !important; }} }}
</style>
<!--[if mso]><style>body,table,td,a,h1,h2,h3,div,span {{font-family:'Times New Roman',Times,serif !important;}}</style><![endif]-->
</head><body style="width:100%;margin:0;padding:0;background:#efede8;font-family:{FONT_STACK};font-size:16px;line-height:1.65;color:#242424;text-align:left;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%">
<div style="display:none;max-height:0;overflow:hidden">최근 행정학 탑저널 신규 논문 {count}편</div>
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" style="width:100%;background:#efede8"><tr><td align="center" class="digest-pad" style="padding:28px 12px">
<!--[if mso]><table role="presentation" width="900" border="0" cellspacing="0" cellpadding="0"><tr><td width="900"><![endif]-->
<table role="presentation" width="100%" border="0" cellspacing="0" cellpadding="0" class="digest-shell" style="width:100%;max-width:900px;background:#ffffff;border-top:5px solid #172c42;font-family:{FONT_STACK}">
  <tr><td class="content-pad" style="padding:30px 36px 27px;border-bottom:1px solid #d9d6cf;font-family:{FONT_STACK};text-align:left">
    <div style="font-family:{FONT_STACK};font-size:12px;line-height:1.2;letter-spacing:1.5px;text-transform:uppercase;color:#8a6b38;text-align:left">Daily research briefing</div>
    <h1 style="margin:8px 0 7px;font-family:{FONT_STACK};font-size:30px;line-height:1.15;color:#172c42;text-align:left">PA Journal Digest</h1>
    <div style="font-family:{FONT_STACK};font-size:15px;line-height:1.5;color:#68635c;text-align:left">{escape(digest_date.strftime('%B %d, %Y'))} &nbsp;·&nbsp; 신규 논문 {count}편 &nbsp;·&nbsp; {len(grouped)}개 저널</div>
  </td></tr>
  <tr><td class="content-pad" style="padding:0 36px;font-family:{FONT_STACK};text-align:left">{''.join(sections)}</td></tr>
  <tr><td class="content-pad" style="padding:23px 36px 27px;font-family:{FONT_STACK};font-size:13px;line-height:1.55;color:#77716a;text-align:left">
    Crossref와 공개 학술 메타데이터를 기반으로 자동 생성되었습니다. 요약은 원문 초록을 대체하지 않습니다.
  </td></tr>
</table>
<!--[if mso]></td></tr></table><![endif]-->
</td></tr></table></body></html>"""
    text_body = (
        f"PA Journal Digest\n{digest_date.isoformat()} · 신규 논문 {count}편\n\n"
        + "\n\n".join(text_sections)
        + "\n\n자동 생성 요약은 원문 초록을 대체하지 않습니다."
    )
    return subject, html_body, text_body
