from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import Article, PreparedBatch
from .render import render_newsletter
from .services import ArticleSummarizer, ResendMailer
from .sources import MetadataClient
from .state import AmbiguousBatchError, StateStore


DEFAULT_STATE = Path("data/state.json")
DEFAULT_OUTPUT = Path("build/batch.json")
NEW_YORK = ZoneInfo("America/New_York")


def _set_github_output(name: str, value: str) -> None:
    output_path = os.getenv("GITHUB_OUTPUT")
    if output_path:
        with Path(output_path).open("a", encoding="utf-8") as handle:
            handle.write(f"{name}={value}\n")


def _batch_identity(articles: list[Article], digest_date: str) -> tuple[str, str]:
    fingerprint = hashlib.sha256(
        "\n".join(sorted(article.stable_id for article in articles)).encode("utf-8")
    ).hexdigest()[:16]
    batch_id = f"{digest_date}-{fingerprint}"
    return batch_id, f"pa-journal-digest-{batch_id}"


def prepare(args: argparse.Namespace) -> int:
    state = StateStore(args.state)
    now = datetime.now(UTC)
    local_today = now.astimezone(NEW_YORK).date()
    if getattr(args, "daily_once", False) and state.has_daily_delivery(local_today.isoformat()):
        _set_github_output("has_batch", "false")
        print(json.dumps({"status": "daily_already_sent", "date": local_today.isoformat()}))
        return 0
    mailto = os.getenv("CROSSREF_MAILTO")
    if not mailto:
        raise RuntimeError("CROSSREF_MAILTO is required")
    metadata = MetadataClient(mailto)
    pending_changed = False
    try:
        active = state.active_prepared_batch(now)
        if active:
            batch_id, batch_state = active
            articles = [metadata.by_public_record(record) for record in batch_state["items"]]
            idempotency_key = batch_state["idempotency_key"]
            created_at = batch_state["created_at"]
            resumed = True
            resent = "-resend-" in batch_id
        elif args.resend_latest:
            latest = state.latest_sent_batch()
            if not latest:
                raise RuntimeError("There is no sent batch to resend")
            original_batch_id, batch_state = latest
            articles = [metadata.by_public_record(record) for record in batch_state["items"]]
            suffix = now.strftime("%Y%m%dT%H%M%SZ")
            batch_id = f"{original_batch_id}-resend-{suffix}"
            idempotency_key = f"pa-journal-digest-{batch_id}"
            created_at = now.isoformat()
            resumed = False
            resent = True
        else:
            start = local_today - timedelta(days=args.lookback_days - 1)
            discovered = metadata.discover(start, local_today)
            candidates = {article.stable_id: article for article in discovered}
            for record in state.pending_records:
                pending_article = metadata.by_public_record(record)
                candidates[pending_article.stable_id] = pending_article
            unsent = [
                article for article in candidates.values() if article.stable_id not in state.sent_ids
            ]
            waiting = [article for article in unsent if not article.abstract]
            articles = [article for article in unsent if article.abstract]
            if not args.dry_run:
                pending_changed = state.update_pending(
                    waiting,
                    {article.stable_id for article in articles},
                    now.isoformat(),
                )
                if pending_changed:
                    state.save()
                    _set_github_output("state_changed", "true")
            batch_id, idempotency_key = _batch_identity(articles, local_today.isoformat())
            if not articles and state.is_batch_sent(batch_id):
                _set_github_output("has_batch", "false")
                print(
                    json.dumps(
                        {
                            "status": "empty_already_sent",
                            "date": local_today.isoformat(),
                            "awaiting_abstract": len(waiting),
                        }
                    )
                )
                return 0
            created_at = now.isoformat()
            resumed = False
            resent = False
    finally:
        metadata.close()

    articles = [article for article in articles if article.abstract]

    summarizer = ArticleSummarizer()
    for article in articles:
        summarizer.summarize(article)
    subject, html, text = render_newsletter(articles, local_today)
    if resent:
        subject = subject.replace("[PA Journal Digest]", "[PA Journal Digest 재발송]", 1)
    prepared = PreparedBatch(
        batch_id=batch_id,
        idempotency_key=idempotency_key,
        created_at=created_at,
        articles=articles,
        subject=subject,
        html=html,
        text=text,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(prepared.model_dump_json(indent=2), encoding="utf-8")
    (args.output.parent / "newsletter.html").write_text(html, encoding="utf-8")
    (args.output.parent / "newsletter.txt").write_text(text, encoding="utf-8")
    if not args.dry_run and not resumed:
        state.prepare(batch_id, idempotency_key, articles, created_at)
        state.save()
    _set_github_output("has_batch", "true")
    _set_github_output("batch_id", batch_id)
    print(
        json.dumps(
            {
                "status": "prepared",
                "batch_id": batch_id,
                "articles": len(articles),
                "awaiting_abstract": len(waiting) if not resumed and not resent else 0,
                "resumed": resumed,
                "resent": resent,
                "dry_run": args.dry_run,
            }
        )
    )
    return 0


def deliver(args: argparse.Namespace) -> int:
    batch = PreparedBatch.model_validate_json(args.input.read_text(encoding="utf-8"))
    state = StateStore(args.state)
    if state.is_batch_sent(batch.batch_id):
        print(json.dumps({"status": "already_sent", "batch_id": batch.batch_id}))
        return 0
    stored = state.data.get("batches", {}).get(batch.batch_id)
    if not stored or stored.get("status") != "prepared":
        raise RuntimeError(f"Batch {batch.batch_id} was not persisted as prepared")
    recipient = os.getenv("NEWSLETTER_TO")
    if not recipient:
        raise RuntimeError("NEWSLETTER_TO is required")
    sender = os.getenv("NEWSLETTER_FROM", "PA Journal Digest <onboarding@resend.dev>")
    mailer = ResendMailer()
    mailer.send(
        sender=sender,
        recipient=recipient,
        subject=batch.subject,
        html=batch.html,
        text=batch.text,
        idempotency_key=batch.idempotency_key,
    )
    sent_at = datetime.now(UTC).isoformat()
    state.mark_sent(batch.batch_id, batch.articles, sent_at)
    state.save()
    print(json.dumps({"status": "sent", "batch_id": batch.batch_id, "articles": len(batch.articles)}))
    return 0


def resolve_batch(args: argparse.Namespace) -> int:
    state = StateStore(args.state)
    batch = state.data.get("batches", {}).get(args.batch_id)
    if not batch:
        raise RuntimeError(f"Unknown batch: {args.batch_id}")
    if batch.get("status") != "prepared":
        raise RuntimeError(f"Batch {args.batch_id} is not prepared")
    if args.action == "retry":
        if not args.confirmed_not_delivered:
            raise RuntimeError("Use --confirmed-not-delivered after checking the Resend dashboard")
        batch["created_at"] = datetime.now(UTC).isoformat()
    else:
        articles = [Article.model_validate(record) for record in batch["items"]]
        state.mark_sent(args.batch_id, articles, datetime.now(UTC).isoformat())
    state.save()
    print(json.dumps({"status": args.action, "batch_id": args.batch_id}))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Daily public administration journal newsletter")
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="Discover, summarize, and render a batch")
    prepare_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    prepare_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    prepare_parser.add_argument("--lookback-days", type=int, default=7)
    prepare_parser.add_argument("--dry-run", action="store_true")
    prepare_parser.add_argument(
        "--daily-once",
        action="store_true",
        help="Skip when a non-resend delivery already succeeded on the New York calendar date",
    )
    prepare_parser.add_argument(
        "--resend-latest",
        action="store_true",
        help="Explicitly resend the most recent sent batch with a new delivery id",
    )
    prepare_parser.set_defaults(func=prepare)

    deliver_parser = subparsers.add_parser("deliver", help="Send a persisted prepared batch")
    deliver_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    deliver_parser.add_argument("--input", type=Path, default=DEFAULT_OUTPUT)
    deliver_parser.set_defaults(func=deliver)

    resolve_parser = subparsers.add_parser("resolve-batch", help="Resolve an ambiguous prepared batch")
    resolve_parser.add_argument("batch_id")
    resolve_parser.add_argument("action", choices=("retry", "mark-sent"))
    resolve_parser.add_argument("--confirmed-not-delivered", action="store_true")
    resolve_parser.add_argument("--state", type=Path, default=DEFAULT_STATE)
    resolve_parser.set_defaults(func=resolve_batch)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if getattr(args, "lookback_days", 1) < 1:
        parser.error("--lookback-days must be at least 1")
    try:
        return int(args.func(args))
    except AmbiguousBatchError as error:
        print(f"DUPLICATE-SAFETY STOP: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
