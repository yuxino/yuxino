"""Regression tests for equal project cards, star ranking and safe API reads."""
from hashlib import sha256
from html import escape
import io
import json
from pathlib import Path
import re
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


def render(counts=None):
    return build_outputs("My intro / 我的介绍", PROJECTS, COUNTS if counts is None else counts, "2026-09-25")


class ProfileTests(unittest.TestCase):
    def test_all_projects_sorted_descending(self):
        ranked = rank_projects(PROJECTS, COUNTS)
        self.assertEqual([COUNTS[p["repo"]] for p in ranked], sorted(COUNTS.values(), reverse=True))
        readme = render()["README.md"]
        positions = [readme.index(f'https://github.com/{p["repo"]}"') for p in ranked]
        self.assertEqual(positions, sorted(positions))

    def test_ties_are_deterministic(self):
        ranked = rank_projects(PROJECTS, dict.fromkeys(COUNTS, 5))
        self.assertEqual([p["name"].casefold() for p in ranked], sorted(p["name"].casefold() for p in PROJECTS))

    def test_daily_changes_reorder_cards(self):
        counts = {**COUNTS, "yuxino/kiri": 1000}
        readme = render(counts)["README.md"]
        self.assertEqual(re.findall(r'<a href="https://github.com/([^"]+)"', readme)[0], "yuxino/kiri")
        self.assertIn("1,000", render(counts)["assets/profile/minimal/kiri-light.svg"])

    def test_every_project_gets_the_same_card(self):
        outputs = render()
        readme = outputs["README.md"]
        self.assertEqual(readme.count("<picture>"), len(PROJECTS))
        self.assertEqual(readme.count('width="380"'), len(PROJECTS))
        self.assertNotIn("<details", readme)
        self.assertNotIn("More projects", readme)
        self.assertNotIn("<table", readme)
        self.assertNotIn('width="49%"', readme)
        self.assertNotIn("style=", readme)
        for project in PROJECTS:
            self.assertEqual(readme.count(f'href="https://github.com/{project["repo"]}"'), 1)
            self.assertIn(escape(project["en"]), readme)
            self.assertIn(escape(project["zh"]), readme)
            slug = project["repo"].split("/")[1].lower()
            for theme in ("light", "dark"):
                self.assertIn(f"assets/profile/minimal/{slug}-{theme}.svg", outputs)

    def test_low_and_zero_star_projects_are_not_downgraded(self):
        outputs = render(dict.fromkeys(COUNTS, 0))
        self.assertEqual(outputs["README.md"].count("<picture>"), len(PROJECTS))
        self.assertEqual(len(outputs), 1 + len(PROJECTS) * 2)

    def test_no_website_links_and_full_stack_intro(self):
        intro = (ROOT / "profile/intro.md").read_text(encoding="utf-8")
        self.assertIn("Full-stack developer", intro)
        self.assertIn("全栈开发", intro)
        readme = build_outputs(intro, PROJECTS, COUNTS, "2026-09-25")["README.md"]
        self.assertNotIn("Frontend developer", readme)
        self.assertNotIn("官网", readme)
        self.assertNotIn("Websites", readme)
        self.assertTrue(all(url.startswith("https://github.com/yuxino/") for url in re.findall(r'href="([^"]+)"', readme)))

    def test_valid_self_contained_svg_in_both_themes(self):
        for project in PROJECTS:
            for dark in (False, True):
                svg = render_card(project, 1234, dark)
                ET.fromstring(svg)
                self.assertIn("1,234", svg)
                for unsafe in ("<script", "<image", "<foreignObject"):
                    self.assertNotIn(unsafe, svg)

    def test_image_cache_keys_follow_content_for_all_projects(self):
        outputs = render()
        links = re.findall(r'(?:src|srcset)="(assets/[^"?]+)\?v=([0-9a-f]+)"', outputs["README.md"])
        self.assertEqual(len(links), len(PROJECTS) * 2)
        for path, version in links:
            self.assertEqual(version, sha256(outputs[path].encode()).hexdigest()[:12])

    def test_identical_input_is_idempotent(self):
        self.assertEqual(render(), render())

    def test_invalid_projects_and_counts_are_rejected(self):
        for projects in ([], PROJECTS + [PROJECTS[0]], [None]):
            with self.assertRaises(ValueError):
                validate_projects(projects)
        for value in (-1, True, None, "100"):
            with self.assertRaises(ValueError):
                rank_projects(PROJECTS, {**COUNTS, PROJECTS[0]["repo"]: value})
        with self.assertRaises(ValueError):
            rank_projects(PROJECTS, {})

    def test_footer_and_replacement_kaomoji(self):
        footer = (ROOT / "profile/footer.md").read_text(encoding="utf-8")
        result = build_outputs("Intro", PROJECTS, COUNTS, "2026-09-25", footer)["README.md"]
        self.assertIn(footer.strip(), result)
        self.assertIn("Issues and PRs", result)
        self.assertIn("我都会认真看", result)
        self.assertEqual(result.count("ฅ(•ㅅ•❀)ฅ"), 1)
        self.assertNotIn("(´｡• ᵕ •｡`)", result)

    def test_api_reads_only_repository_metadata(self):
        body = b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}'
        with patch.object(updater, "urlopen", return_value=io.BytesIO(body)) as request:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        self.assertEqual(request.call_args.args[0].full_url, "https://api.github.com/repos/yuxino/kiri")

    def test_private_missing_and_invalid_counts_are_rejected(self):
        valid = dict(full_name="yuxino/kiri", private=False, stargazers_count=5)
        invalid = [{k: v for k, v in valid.items() if k != "stargazers_count"}, {**valid, "private": True}, {**valid, "stargazers_count": True}, {**valid, "stargazers_count": -1}, {**valid, "full_name": "yuxino/other"}]
        for data in invalid:
            with patch.object(updater, "urlopen", return_value=io.BytesIO(json.dumps(data).encode())), self.assertRaises(ValueError):
                updater.fetch_stars("yuxino/kiri")

    def test_transient_api_errors_are_retried(self):
        error = HTTPError("https://api.github.com/repos/yuxino/kiri", 503, "Unavailable", {}, None)
        body = io.BytesIO(b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}')
        with patch.object(updater, "urlopen", side_effect=[error, body]), patch.object(updater.time, "sleep") as sleep:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        sleep.assert_called_once_with(1)

    def fixture(self, root):
        (root / "profile").mkdir()
        (root / "profile/projects.json").write_text(json.dumps(PROJECTS))
        (root / "profile/intro.md").write_text("Original intro")
        (root / "profile/footer.md").write_text("Original footer")
        (root / "README.md").write_text("Original README")

    def test_failed_api_read_changes_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[500, RuntimeError("API unavailable")]):
                with self.assertRaises(RuntimeError):
                    updater.main()
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_successful_main_writes_all_cards_and_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[COUNTS[p["repo"]] for p in PROJECTS]):
                updater.main()
            self.assertEqual(json.loads((root / "profile/stars.json").read_text())["counts"], COUNTS)
            self.assertEqual(len(list((root / "assets/profile/minimal").glob("*.svg"))), len(PROJECTS) * 2)
            readme = (root / "README.md").read_text()
            self.assertIn("Original intro", readme)
            self.assertIn("Original footer", readme)
            self.assertEqual(readme.count("<picture>"), len(PROJECTS))


if __name__ == "__main__":
    unittest.main()
