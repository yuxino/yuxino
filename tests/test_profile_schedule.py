"""Keep the daily schedule, snapshot date and displayed timezone consistent."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_stars as updater


class ProfileScheduleTests(unittest.TestCase):
    def test_one_daily_schedule_at_beijing_midnight(self):
        workflow = (ROOT / ".github/workflows/update-stars.yml").read_text(encoding="utf-8")
        schedules = re.findall(r"^\s+- cron: '([^']+)'", workflow, re.MULTILINE)
        timezones = re.findall(r'^\s+timezone: "([^"]+)"', workflow, re.MULTILINE)
        self.assertEqual(schedules, ["0 0 * * *"])
        self.assertEqual(timezones, ["Asia/Shanghai"])
        self.assertEqual(updater.PROFILE_TIMEZONE.key, timezones[0])

    def test_date_rolls_over_at_beijing_midnight_not_utc_midnight(self):
        projects = [{
            "repo": "yuxino/kiri", "name": "Kiri", "icon": "capture",
            "en": "Screenshots and recording.", "zh": "截图与录屏。"
        }]
        cases = [
            (datetime(2026, 9, 25, 15, 59, 59, tzinfo=timezone.utc), "2026-09-25"),
            (datetime(2026, 9, 25, 16, 0, 0, tzinfo=timezone.utc), "2026-09-26"),
            (datetime(2026, 9, 25, 16, 30, 0, tzinfo=timezone.utc), "2026-09-26"),
        ]
        for instant, expected_date in cases:
            with self.subTest(instant=instant), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "profile").mkdir()
                (root / "profile/projects.json").write_text(json.dumps(projects), encoding="utf-8")
                (root / "profile/intro.md").write_text("Full-stack developer / 全栈开发", encoding="utf-8")
                (root / "profile/footer.md").write_text("Thanks / 谢谢", encoding="utf-8")
                with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", return_value=123), patch.object(updater, "datetime") as clock:
                    clock.now.side_effect = lambda tz: instant.astimezone(tz)
                    updater.main()
                    clock.now.assert_called_once_with(updater.PROFILE_TIMEZONE)
                snapshot = json.loads((root / "profile/stars.json").read_text(encoding="utf-8"))
                readme = (root / "README.md").read_text(encoding="utf-8")
                self.assertEqual(snapshot["date"], expected_date)
                self.assertEqual(snapshot["timezone"], "Asia/Shanghai")
                self.assertEqual(snapshot["counts"], {"yuxino/kiri": 123})
                self.assertIn(f"{expected_date} (UTC+8)", readme)
                self.assertNotIn("(UTC)", readme)


if __name__ == "__main__":
    unittest.main()
