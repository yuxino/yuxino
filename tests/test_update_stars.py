"""Regression tests for single-line text, folding, hidden counts and safe reads."""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import update_stars as updater
from render_profile import FEATURED_COUNT, build_outputs, rank_projects, render_project, validate_projects

PROJECTS = json.loads((ROOT / "profile/projects.json").read_text(encoding="utf-8"))
COUNTS = {p["repo"]: i for i, p in enumerate(PROJECTS)}


def render(counts=None, date="2026-09-27"):
    return build_outputs("My intro / 我的介绍", PROJECTS, COUNTS if counts is None else counts, date)


class ProfileTests(unittest.TestCase):
    def test_all_projects_remain_sorted_descending(self):
        ranked = rank_projects(PROJECTS, COUNTS)
        self.assertEqual([COUNTS[p["repo"]] for p in ranked], sorted(COUNTS.values(), reverse=True))
        links = re.findall(r'href="https://github.com/([^"]+)"', render()["README.md"])
        self.assertEqual(links, [p["repo"] for p in ranked])

    def test_ties_are_deterministic(self):
        ranked = rank_projects(PROJECTS, dict.fromkeys(COUNTS, 5))
        self.assertEqual([p["name"].casefold() for p in ranked], sorted(p["name"].casefold() for p in PROJECTS))

    def test_daily_changes_reorder_text_without_exposing_counts(self):
        readme = render({**COUNTS, "yuxino/kiri": 987654})["README.md"]
        self.assertEqual(re.findall(r'<a href="https://github.com/([^"]+)"', readme)[0], "yuxino/kiri")
        self.assertNotIn("987654", readme)
        self.assertNotIn("987,654", readme)

    def test_one_bilingual_text_line_per_project(self):
        readme = render()["README.md"]
        rows = [line for line in readme.splitlines() if line.startswith('<a href=')]
        self.assertEqual(len(rows), len(PROJECTS))
        for project in PROJECTS:
            row = next(line for line in rows if f'/{project["repo"]}"' in line)
            self.assertEqual(row.removesuffix("<br>"), render_project(project))
            self.assertIn(escape(project["en"]), row)
            self.assertIn(escape(project["zh"]), row)
        for obsolete in ("<picture", "<img", "<svg", "<table", "assets/", "style=", "width=", "☆", "Updated daily", "UTC+8"):
            self.assertNotIn(obsolete, readme)
        self.assertEqual(set(render()), {"README.md"})

    def test_other_projects_stay_folded_with_the_same_text_style(self):
        before, separator, rest = render()["README.md"].partition("<details>")
        folded, closing, after = rest.partition("</details>")
        self.assertTrue(separator and closing)
        self.assertEqual(before.count('<a href='), FEATURED_COUNT)
        self.assertEqual(folded.count('<a href='), len(PROJECTS) - FEATURED_COUNT)
        self.assertIn("<summary>Other projects / 其他项目</summary>", folded)
        self.assertNotIn("<details open", render()["README.md"])
        self.assertNotIn('<a href=', after)
        for project in rank_projects(PROJECTS, COUNTS)[FEATURED_COUNT:]:
            self.assertIn(render_project(project), folded)

    def test_small_list_has_no_empty_other_section(self):
        for size in (1, FEATURED_COUNT):
            projects = PROJECTS[:size]
            counts = {p["repo"]: COUNTS[p["repo"]] for p in projects}
            readme = build_outputs("Intro", projects, counts, "2026-09-27")["README.md"]
            self.assertNotIn("<details", readme)
            self.assertEqual(readme.count('<a href='), size)

    def test_zero_count_projects_are_kept(self):
        self.assertEqual(render(dict.fromkeys(COUNTS, 0))["README.md"].count('<a href='), len(PROJECTS))

    def test_count_and_date_changes_do_not_change_page_if_order_is_same(self):
        self.assertEqual(render(), render({repo: n + 100 for repo, n in COUNTS.items()}, "2026-09-28"))

    def test_full_stack_intro_and_cute_footer_are_preserved(self):
        intro = (ROOT / "profile/intro.md").read_text(encoding="utf-8")
        footer = (ROOT / "profile/footer.md").read_text(encoding="utf-8")
        readme = build_outputs(intro, PROJECTS, COUNTS, "2026-09-27", footer)["README.md"]
        self.assertIn(intro.strip(), readme)
        self.assertIn(footer.strip(), readme)
        self.assertIn("Full-stack developer", readme)
        self.assertIn("全栈开发", readme)
        self.assertIn("Issues and PRs", readme)
        self.assertIn("我都会认真看", readme)
        self.assertEqual(readme.count("(っ˘ω˘ς )♡"), 1)
        self.assertGreater(readme.index(footer.strip()), readme.index("</details>"))
        self.assertNotIn("Frontend developer", readme)
        self.assertNotIn("官网", readme)
        self.assertTrue(all(url.startswith("https://github.com/yuxino/") for url in re.findall(r'href="([^"]+)"', readme)))

    def test_text_is_escaped_instead_of_interpreted_as_html(self):
        project = {**PROJECTS[0], "name": '<img src="x">', "en": 'A & B', "zh": '<script>测试</script>'}
        row = render_project(project)
        self.assertIn('&lt;img', row)
        self.assertIn('A &amp; B', row)
        self.assertNotIn('<img', row)
        self.assertNotIn('<script>', row)

    def test_invalid_projects_and_counts_are_rejected(self):
        for projects in ([], PROJECTS + [PROJECTS[0]], [None], [{**PROJECTS[0], "en": "two\nlines"}]):
            with self.assertRaises(ValueError):
                validate_projects(projects)
        for value in (-1, True, None, "100"):
            with self.assertRaises(ValueError):
                rank_projects(PROJECTS, {**COUNTS, PROJECTS[0]["repo"]: value})
        with self.assertRaises(ValueError):
            rank_projects(PROJECTS, {})

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
        (root / "profile/projects.json").write_text(json.dumps(PROJECTS), encoding="utf-8")
        (root / "profile/intro.md").write_text("Original intro", encoding="utf-8")
        (root / "profile/footer.md").write_text("Original footer", encoding="utf-8")
        (root / "README.md").write_text("Original README", encoding="utf-8")

    def test_failed_api_read_changes_no_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            before = {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[500, RuntimeError("API unavailable")]):
                with self.assertRaises(RuntimeError):
                    updater.main()
            self.assertEqual(before, {str(p): p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_successful_main_writes_text_and_snapshot_without_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.fixture(root)
            with patch.object(updater, "ROOT", root), patch.object(updater, "fetch_stars", side_effect=[COUNTS[p["repo"]] for p in PROJECTS]):
                updater.main()
            self.assertEqual(json.loads((root / "profile/stars.json").read_text())["counts"], COUNTS)
            self.assertFalse((root / "assets").exists())
            readme = (root / "README.md").read_text(encoding="utf-8")
            self.assertIn("Original intro", readme)
            self.assertIn("Original footer", readme)
            self.assertEqual(readme.count('<a href='), len(PROJECTS))
            self.assertEqual(readme.count("<details>"), 1)

    def test_workflow_no_longer_commits_generated_cards(self):
        workflow = (ROOT / ".github/workflows/update-stars.yml").read_text(encoding="utf-8")
        self.assertIn("git add README.md profile/stars.json\n", workflow)
        self.assertNotIn("assets/profile/minimal", workflow)


if __name__ == "__main__":
    unittest.main()
