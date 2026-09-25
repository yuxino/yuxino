"""Offline tests: sorting, rendering, public-count validation, failure safety."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_stars as updater
from render_profile import build_outputs, rank_projects, render_card, validate_projects

PROJECTS = json.loads((ROOT / "profile/projects.json").read_text(encoding="utf-8"))
COUNTS = {p["repo"]: i for i, p in enumerate(PROJECTS)}


class ProfileTests(unittest.TestCase):
    def test_all_projects_are_globally_sorted_descending(self):
        ranked = rank_projects(PROJECTS, COUNTS)
        self.assertEqual([COUNTS[p["repo"]] for p in ranked], sorted(COUNTS.values(), reverse=True))
        readme = build_outputs("My intro", PROJECTS, COUNTS, "2026-09-25")["README.md"]
        positions = [readme.index(f'https://github.com/{p["repo"]}"') for p in ranked]
        self.assertEqual(positions, sorted(positions))

    def test_ties_use_deterministic_alphabetical_order(self):
        counts = {p["repo"]: 5 for p in PROJECTS}
        ranked = rank_projects(PROJECTS, counts)
        self.assertEqual([p["name"].casefold() for p in ranked], sorted(p["name"].casefold() for p in PROJECTS))

    def test_daily_changes_promote_projects_into_featured_six(self):
        counts = dict(COUNTS)
        old_top = rank_projects(PROJECTS, counts)[0]["repo"]
        counts["yuxino/kiri"] = 1000
        outputs = build_outputs("Intro", PROJECTS, counts, "2026-09-25")
        self.assertIn("assets/profile/minimal/kiri-light.svg", outputs)
        self.assertLess(outputs["README.md"].index('https://github.com/yuxino/kiri"'), outputs["README.md"].index(f'https://github.com/{old_top}"'))

    def test_render_keeps_intro_and_both_languages(self):
        outputs = build_outputs("My custom intro / 我的介绍", PROJECTS, COUNTS, "2026-09-25")
        readme = outputs["README.md"]
        self.assertIn("My custom intro / 我的介绍", readme)
        self.assertEqual(readme.count("<picture>"), 6)
        self.assertEqual(readme.count("<details>"), 1)
        self.assertNotIn("<table", readme)
        self.assertNotIn('width="49%"', readme)
        for project in PROJECTS:
            self.assertIn(project["zh"], readme)
            self.assertIn(project["web"].replace("&", "&amp;"), readme)

    def test_both_themes_produce_valid_self_contained_svg(self):
        for project in PROJECTS:
            for dark in (False, True):
                svg = render_card(project, 1234, dark)
                ET.fromstring(svg)
                self.assertIn("1,234", svg)
                self.assertNotIn("<script", svg)
                self.assertNotIn("<image", svg)
                self.assertNotIn("<foreignObject", svg)

    def test_identical_input_is_idempotent(self):
        args = ("Intro", PROJECTS, COUNTS, "2026-09-25")
        self.assertEqual(build_outputs(*args), build_outputs(*args))

    def test_curated_list_and_counts_are_validated(self):
        for projects in ([], PROJECTS + [PROJECTS[0]]):
            with self.assertRaises(ValueError):
                validate_projects(projects)
        for count in (-1, True, None, "100"):
            with self.subTest(count=count), self.assertRaises(ValueError):
                rank_projects(PROJECTS, {**COUNTS, PROJECTS[0]["repo"]: count})
        with self.assertRaises(ValueError):
            rank_projects(PROJECTS, {})

    def test_failed_api_read_leaves_all_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "profile").mkdir()
            (root / "profile/projects.json").write_text(json.dumps(PROJECTS))
            (root / "profile/intro.md").write_text("Original intro")
            (root / "profile/footer.md").write_text("Original footer")
            (root / "README.md").write_text("Original README")
            before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[500, RuntimeError("API unavailable")]):
                with self.assertRaises(RuntimeError):
                    updater.main()
            after = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            self.assertEqual(before, after)

    def test_api_reads_only_repository_metadata(self):
        body = b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}'
        with patch.object(updater, "urlopen", return_value=io.BytesIO(body)) as request:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        self.assertEqual(request.call_args.args[0].full_url, "https://api.github.com/repos/yuxino/kiri")

    def test_invalid_or_private_api_values_are_rejected(self):
        invalid = [{"full_name": "yuxino/kiri", "private": False}, {"full_name": "yuxino/kiri", "private": True, "stargazers_count": 5}, {"full_name": "yuxino/kiri", "private": False, "stargazers_count": True}, {"full_name": "yuxino/other", "private": False, "stargazers_count": 5}]
        for data in invalid:
            with patch.object(updater, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())), self.assertRaises(ValueError):
                updater.fetch_stars("yuxino/kiri")

    def test_transient_api_errors_are_retried(self):
        error = HTTPError("https://api.github.com/repos/yuxino/kiri", 503, "Unavailable", {}, None)
        body = io.BytesIO(b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}')
        with patch.object(updater, "urlopen", side_effect=[error, body]), patch.object(updater.time, "sleep") as sleep:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        sleep.assert_called_once_with(1)

    def test_successful_main_writes_sorted_profile_and_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "profile").mkdir()
            (root / "profile/projects.json").write_text(json.dumps(PROJECTS))
            (root / "profile/intro.md").write_text("Custom intro")
            (root / "profile/footer.md").write_text("Custom footer")
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[COUNTS[p["repo"]] for p in PROJECTS]):
                updater.main()
            snapshot = json.loads((root / "profile/stars.json").read_text())
            self.assertEqual(snapshot["counts"], COUNTS)
            self.assertEqual(len(list((root / "assets/profile/minimal").glob("*.svg"))), 12)
            self.assertIn("Custom intro", (root / "README.md").read_text())
            self.assertIn("Custom footer", (root / "README.md").read_text())

    def test_footer_keeps_both_languages_and_kaomoji(self):
        footer = (ROOT / "profile/footer.md").read_text(encoding="utf-8")
        result = build_outputs("Intro", PROJECTS, COUNTS, "2026-09-25", footer)["README.md"]
        self.assertIn(footer.strip(), result)
        self.assertIn("Issues and PRs", result)
        self.assertIn("我都会认真看", result)
        self.assertEqual(result.count("(´｡• ᵕ •｡`)"), 1)

    def test_image_cache_keys_follow_card_content(self):
        import re
        outputs = build_outputs("Intro", PROJECTS, COUNTS, "2026-09-25")
        links = re.findall(r'(?:src|srcset)="(assets/[^"?]+)\?v=([0-9a-f]+)"', outputs["README.md"])
        self.assertEqual(len(links), 12)
        from hashlib import sha256
        for path, version in links:
            self.assertIn(path, outputs)
            self.assertEqual(version, sha256(outputs[path].encode()).hexdigest()[:12])

    def test_featured_cards_are_readable_at_narrow_widths(self):
        outputs = build_outputs("Intro", PROJECTS, COUNTS, "2026-09-25")
        self.assertEqual(outputs["README.md"].count('width="380"'), 6)
        self.assertNotIn('<table', outputs["README.md"])
        self.assertNotIn('style=', outputs["README.md"])


if __name__ == "__main__":
    unittest.main()
