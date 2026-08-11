from pathlib import Path


def test_daily_schedule_starts_early_to_target_830_delivery() -> None:
    workflow = Path(".github/workflows/daily-digest.yml").read_text(encoding="utf-8")

    for cron in ("15 7 * * *", "35 7 * * *", "55 7 * * *"):
        assert f'cron: "{cron}"' in workflow
    assert workflow.count('timezone: "America/New_York"') == 3
