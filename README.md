# PA Journal Digest

매일 미국 동부시간 오전 7:30에 주요 행정학 저널의 최근 온라인 출간 논문을 확인하고,
새 논문이 있을 때만 저자·공개 소속 정보, 영문 초록, 한국어 1–2문장 요약을 이메일로 보냅니다.

## Monitored journals

| Short name | Journal |
|---|---|
| JPART | Journal of Public Administration Research and Theory |
| PAR | Public Administration Review |
| Governance | Governance |
| PA | Public Administration |
| PMR | Public Management Review |
| PSJ | Policy Studies Journal |
| GIQ | Government Information Quarterly |
| ARPA | The American Review of Public Administration |
| IPMJ | International Public Management Journal |
| PPMG | Perspectives on Public Management and Governance |
| A&S | Administration & Society |
| PPMR | Public Performance & Management Review |
| ROPPA | Review of Public Personnel Administration |

뉴스레터에서는 위 표의 순서대로, 행정학 분야의 일반적인 저널 위상과 최신 영향력 지표를 반영해
섹션을 배치합니다. 특정 날짜에 신규 논문이 없는 저널은 표시하지 않습니다.

## How it works

1. Crossref에서 각 저널의 ISSN과 최근 7일 출간일을 기준으로 논문을 찾습니다.
2. Crossref에 초록이나 저자 소속이 없으면 Semantic Scholar와 OpenAlex의 공개 메타데이터를 확인합니다.
3. 명백한 서평, 정정, 철회, 목차, 편집자 서문은 제외합니다.
4. OpenAI가 초록에 근거한 한국어 요약을 생성합니다. 초록이 없으면 제목 기반임을 명시합니다.
5. Resend가 HTML 및 일반 텍스트 뉴스레터를 발송합니다.
6. `data/state.json`에 DOI 기반 발송 원장을 기록하여 같은 논문을 다시 보내지 않습니다.

## GitHub setup

Repository **Settings → Secrets and variables → Actions**에서 다음 값을 등록합니다.

### Secrets

| Name | Value |
|---|---|
| `OPENAI_API_KEY` | 새로 발급한 OpenAI API 키 |
| `RESEND_API_KEY` | Resend API 키 |
| `CROSSREF_MAILTO` | Crossref polite-pool 연락처 이메일 |
| `NEWSLETTER_TO` | 뉴스레터 수신 이메일 |

API 키를 코드, 커밋, Issue, 채팅에 붙여 넣지 마세요. 노출된 키는 폐기하고 새 키를 발급해야 합니다.

### Variables (optional)

| Name | Default |
|---|---|
| `OPENAI_MODEL` | `gpt-5.6-luna` |
| `NEWSLETTER_FROM` | `PA Journal Digest <onboarding@resend.dev>` |

`onboarding@resend.dev`는 Resend 계정에 등록된 본인 이메일로만 보낼 수 있습니다. 다른 주소로
발송하려면 Resend에서 소유 도메인을 인증하고 `NEWSLETTER_FROM`을 해당 도메인 주소로 변경하세요.

저장소 **Settings → Actions → General → Workflow permissions**에서 **Read and write permissions**가
허용되어야 Actions가 발송 원장을 커밋할 수 있습니다.

## First run

1. Actions 탭에서 **Daily PA Journal Digest**를 선택합니다.
2. **Run workflow**에서 `dry_run=true`로 실행합니다.
3. 실행 artifact의 `newsletter.html`을 확인합니다.
4. 문제가 없으면 `dry_run=false`로 다시 실행합니다. 최초 실발송에는 최근 7일 논문이 포함됩니다.

새 논문이 없으면 메일을 보내지 않습니다. 예약 실행은 GitHub Actions 부하에 따라 다소 늦어질 수 있습니다.

## Duplicate-safety recovery

발송 요청 후 원장 커밋 전에 작업이 중단되면 배치가 `prepared` 상태로 남습니다. 24시간 안에는 같은
Resend idempotency key로 안전하게 재시도합니다. 24시간이 지나면 자동 전송을 중단합니다.

Resend 대시보드에서 배달되지 않았음을 확인한 경우:

```bash
pa-digest resolve-batch BATCH_ID retry --confirmed-not-delivered
```

이미 배달된 것이 확인된 경우:

```bash
pa-digest resolve-batch BATCH_ID mark-sent
```

변경된 `data/state.json`을 커밋한 뒤 workflow를 다시 실행합니다.

## Local checks

```bash
python -m pip install -e ".[test]"
pytest
```

로컬 미리보기에는 실제 메타데이터 및 OpenAI API 키가 필요합니다.

```bash
pa-digest prepare --dry-run --lookback-days 7
```
