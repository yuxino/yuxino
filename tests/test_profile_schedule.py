"""Keep automatic profile updates disabled and internal snapshot dates consistent."""
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
    def test_profile_updates_are_manual_only(self):
        workflow = (ROOT / ".github/workflows/update-stars.yml").read_text(encoding="utf-8")
        triggers = re.search(r"(?ms)^on:\n(.*?)(?=^[^\s#]|\Z)", workflow)
        self.assertIsNotNone(triggers)
        active_lines = [
            line.strip() for line in triggers.group(1).splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        self.assertEqual(active_lines, ["workflow_dispatch:"])
        self.assertNotRegex(workflow, r"(?m)^\s+- cron:")
        self.assertEqual(updater.PROFILE_TIMEZONE.key, "Asia/Shanghai")

    def test_date_rolls_over_in_snapshot_without_appearing_on_profile(self):
        projects = [{
            "repo": "yuxino/kiri", "name": "Kiri",
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
                self.assertNotIn(expected_date, readme)
                self.assertNotIn("UTC", readme)
                self.assertNotIn("123", readme)


if __name__ == "__main__":
    unittest.main()
