# PA Journal Digest

Every day, aiming for delivery by 7:00 a.m. US Eastern Time, this project checks major public
administration and political science journals for recently published online articles. When there
are new articles, it emails each one with its authors and their public affiliations, the English
abstract, and a one- to two-sentence summary in Korean.
Each article also carries three or four short tags for its research area, method, and key concepts.
Method tags look like `서베이 (패널 설문)` (survey, panel), `준실험 (이중차분)` (quasi-experiment,
difference-in-differences), or `이론/개념 (개념적 모형)` (theory/conceptual, conceptual model).
On days with no new articles, it still sends one email confirming that the check ran.

## Monitored journals

Tiers follow SCImago Journal Rank (SJR) 2025, retrieved on 2026-11-28 from
[scimagojr.com](https://www.scimagojr.com/) (Scopus data as of March 2026). The rank column is the
journal's position in its main SCImago subject category. Within each field:

- **Tier 1**: the top few journals of the field, cut where SJR drops sharply. Public administration
  journals are ranked within SCImago's Public Administration category.
- **Tier 2**: other Q1 journals with SJR ≥ 1.5.
- **Tier 3**: SJR below 1.5, or not indexed in Scopus.

The same numbers are recorded next to each journal in `src/pa_digest/config.py`.

| Field | Short name | Journal | SJR 2025 | Rank in SCImago category | Tier |
|---|---|---|---:|---|---:|
| Public administration & policy | PAR | Public Administration Review | 3.305 | Public Administration #2/246 | 1 |
| | JPART | Journal of Public Administration Research and Theory | 3.301 | Public Administration #3/246 | 1 |
| | PA | Public Administration | 2.723 | Public Administration #4/246 | 2 |
| | PMR | Public Management Review | 2.540 | Public Administration #5/246 | 2 |
| | GIQ | Government Information Quarterly | 3.575 | Sociology & Political Science #13/1513 (not in Public Administration) | 2 |
| | PPMG | Perspectives on Public Management and Governance | 1.988 | Public Administration #8/246 | 2 |
| | ROPPA | Review of Public Personnel Administration | 1.952 | Public Administration #9/246 | 2 |
| | JPAM | Journal of Policy Analysis and Management | 1.741 | Public Administration #12/246 | 2 |
| | Governance | Governance | 1.581 | Public Administration #13/246 | 2 |
| | PSJ | Policy Studies Journal | 1.363 | Public Administration #20/246 | 3 |
| | IPMJ | International Public Management Journal | 1.226 | Public Administration #27/246 | 3 |
| | ARPA | The American Review of Public Administration | 1.221 | Public Administration #28/246 | 3 |
| | PPMR | Public Performance & Management Review | 1.097 | Public Administration #34/246 | 3 |
| | A&S | Administration & Society | 1.073 | Public Administration #37/246 | 3 |
| | JBPA | Journal of Behavioral Public Administration | — | Not indexed in Scopus | 3 |
| Political science | AJPS | American Journal of Political Science | 6.539 | Political Science & IR #1/725 | 1 |
| | APSR | American Political Science Review | 5.433 | Political Science & IR #2/725 | 1 |
| | PolAnalysis | Political Analysis | 4.368 | Political Science & IR #3/725 | 1 |
| | JOP | The Journal of Politics | 3.492 | Sociology & Political Science #15/1513 | 2 |
| | PolBeh | Political Behavior | 2.955 | Sociology & Political Science #26/1513 | 2 |
| | PolComm | Political Communication | 2.907 | Sociology & Political Science #27/1513 | 2 |
| | POQ | Public Opinion Quarterly | 2.191 | Sociology & Political Science #43/1513 | 2 |
| | JEPS | Journal of Experimental Political Science | 2.016 | Sociology & Political Science #50/1513 | 2 |
| Management & organizations | AMA | Academy of Management Annals | 14.367 | Organizational Behavior & HRM #2/262 | 1 |
| | AMJ | Academy of Management Journal | 10.781 | Strategy & Management #3/518 | 1 |
| | SMJ | Strategic Management Journal | 10.154 | Strategy & Management #4/518 | 1 |
| | AMR | Academy of Management Review | 9.996 | Strategy & Management #5/518 | 1 |
| | JOM | Journal of Management | 8.251 | Strategy & Management #6/518 | 2 |
| | OrgSci | Organization Science | 7.929 | Organizational Behavior & HRM #3/262 | 2 |
| | JAP | Journal of Applied Psychology | 5.473 | Applied Psychology #3/270 | 2 |
| | JOB | Journal of Organizational Behavior | 3.999 | Organizational Behavior & HRM #12/262 | 2 |
| | OBHDP | Organizational Behavior and Human Decision Processes | 3.152 | Organizational Behavior & HRM #15/262 | 2 |
| Psychology (AI-related articles only) | PsychBull | Psychological Bulletin | 8.496 | Psychology (misc.) #2/347 | 1 |
| | JPSP | Journal of Personality and Social Psychology | 3.767 | Social Psychology #4/318 | 2 |
| | PsychSci | Psychological Science | 2.309 | Psychology (misc.) #17/347 | 2 |
| | PSPB | Personality and Social Psychology Bulletin | 2.086 | Social Psychology #13/318 | 2 |
| Information systems | ISR | Information Systems Research | 5.679 | Management Information Systems #2/144 | 1 |
| | MISQ | MIS Quarterly | 4.061 | Management Information Systems #3/144 | 1 |
| AI & social science (AI-related political and psychological articles only) | Nature | Nature | 19.713 | Multidisciplinary #1/233 | 1 |
| | Science | Science | 10.948 | Multidisciplinary #2/233 | 1 |
| | NHB | Nature Human Behaviour | 4.896 | Social Psychology #3/318 | 2 |
| | PNAS | Proceedings of the National Academy of Sciences | 3.283 | Multidisciplinary #7/233 | 2 |

NHB, PNAS, Science, and Nature cover very broad ground, and for the psychology journals (JPSP, PSPB,
Psychological Science, Psychological Bulletin) only AI-related research is wanted, so these journals
are not taken in full. Each day the titles and abstracts of the candidate articles are sent together
to `OPENAI_MODEL`, which keeps only articles where AI is the central topic and the paper addresses a
political science or psychology question such as politics, government, public opinion, persuasion,
beliefs, or trust. Reference examples for this judgment are the study by Costello, Pennycook, and
Rand on reducing conspiracy beliefs through conversations with an LLM, and the study by Myra Cheng
and colleagues on LLM sycophancy. Studies that use machine learning only as a measurement tool, and
AI research in biology, medicine, or physics (for example, a chromatin biology assessment of
AlphaFold3), are excluded by both checks. Social science articles that are not
about AI (for example, sleep deprivation and phishing, or bureaucratic incentives under China's
one-child policy) are also excluded. Articles that pass this screen are judged again, one by one,
for AI relevance at the summary stage, and are sent only when both judgments are "yes". For these
four journals, news, commentary (Comment, Perspective, News & Views), replies (Reply to), and
editorials are also dropped, leaving only original research and review articles. Nature articles
with `10.1038/d41586-` DOIs are all news or commentary and are excluded.

The newsletter groups sections by field and lists journals in the order of the table above. A
journal with no new articles on a given day does not appear in that day's email. On days with no
new articles at all, only the confirmation notice is sent.

## How it works

1. Crossref is queried for each journal's articles by ISSN and a publication date within the last
   seven days.
2. If Crossref lacks an abstract or author affiliations, public metadata from Semantic Scholar and
   OpenAlex is checked. An incomplete abstract is treated as missing and the next source is tried:
   fewer than 50 words, a snippet cut off with `...`, a fragment starting mid-sentence, or an image
   URL scraped in place of the abstract. Articles without a complete abstract are not sent; they are
   held on a waiting list and sent later once an abstract becomes available.
3. Obvious book reviews, corrections, retractions, and tables of contents are excluded. Editorials,
   editor's notes, and special-issue or symposium introductions are first filtered by title; any
   that the title filter misses are identified and dropped by OpenAI at the summary stage. Items
   dropped this way are recorded under `skipped` in `data/state.json` so they are not summarized
   again.
4. OpenAI writes a Korean summary grounded in the abstract, plus field, method, and key-concept tags.
5. Resend sends the newsletter as HTML and plain text.
6. A DOI-based delivery ledger is written to `data/state.json` so the same article is never sent
   twice.

## GitHub setup

Add the following under the repository's **Settings → Secrets and variables → Actions**.

### Secrets

| Name | Value |
|---|---|
| `OPENAI_API_KEY` | A newly issued OpenAI API key |
| `RESEND_API_KEY` | Resend API key |
| `CROSSREF_MAILTO` | Contact email for the Crossref polite pool |
| `NEWSLETTER_TO` | Email address that receives the newsletter |

Never paste API keys into code, commits, issues, or chats. If a key is exposed, revoke it and issue
a new one.

### Variables (optional)

| Name | Default |
|---|---|
| `OPENAI_MODEL` | `gpt-6-luna` |
| `NEWSLETTER_FROM` | `PA Journal Digest <onboarding@resend.dev>` |

`onboarding@resend.dev` can only send to your own email address registered with your Resend
account. To send to other addresses, verify a domain you own in Resend and change `NEWSLETTER_FROM`
to an address on that domain.

Under the repository's **Settings → Actions → General → Workflow permissions**, **Read and write
permissions** must be allowed so that Actions can commit the delivery ledger.

## First run

1. In the Actions tab, select **Daily PA Journal Digest**.
2. Under **Run workflow**, run it with `dry_run=true`.
3. Check `newsletter.html` in the run's artifact.
4. If everything looks right, run it again with `dry_run=false`. The first real delivery includes
   articles from the last seven days.

If there are no new articles, a notice email saying `오늘은 새로 확인된 논문이 없습니다` ("No new
articles were found today") is sent. Scheduled runs can be delayed depending on GitHub Actions load.

Turn on `resend_latest` in a manual run only when the latest batch that was already sent needs to be
sent again with the current design. To rebuild and resend the recent window (`lookback_days`) from
scratch with the current filters, turn on `include_sent`. This re-screens and re-summarizes articles
that were already sent, and it does not count toward the regular daily delivery.
Scheduled runs always have these options turned off, so they do not affect routine duplicate
protection.

## Duplicate-safety recovery

If a job stops after the send request but before the ledger commit, the batch is left in the
`prepared` state. Within 24 hours it is retried safely with the same Resend idempotency key. After 24
hours, automatic sending stops.

GitHub has been starting scheduled runs 7–12 hours late (in late November 2026, emails arrived
between about 9:30 a.m. and 1:40 p.m. ET), so the workflow is scheduled three times, at 12:05,
12:25, and 12:45 a.m. Eastern Time, just after midnight so that every run still falls on the same
Eastern date. The cron entries use `timezone: "America/New_York"`, so they follow daylight saving
time. When a new scheduled run starts, any earlier run still in progress is cancelled so runs do
not pile up. Only the first successful run sends; later runs exit through the once-a-day guard.

If you confirm in the Resend dashboard that the email was not delivered:

```bash
pa-digest resolve-batch BATCH_ID retry --confirmed-not-delivered
```

If you confirm that it was delivered:

```bash
pa-digest resolve-batch BATCH_ID mark-sent
```

Then commit the changed `data/state.json` and run the workflow again.

## Local checks

```bash
python -m pip install -e ".[test]"
pytest
```

A local preview needs real metadata access and an OpenAI API key.

```bash
pa-digest prepare --dry-run --lookback-days 7
```
