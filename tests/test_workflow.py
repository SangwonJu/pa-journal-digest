from pathlib import Path


def test_daily_schedule_starts_early_to_target_7am_delivery() -> None:
    workflow = Path(".github/workflows/daily-digest.yml").read_text(encoding="utf-8")

    for cron in ("15 6 * * *", "35 6 * * *", "55 6 * * *"):
        assert f'cron: "{cron}"' in workflow
    assert workflow.count('timezone: "America/New_York"') == 3
    assert "cancel-in-progress: true" in workflow
