"""Offline regression tests for the profile updater (standard library only)."""
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_stars", ROOT / "scripts/update_stars.py")
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)

SAMPLE = """Keep my links, descriptions and layout. / 保留双语介绍。
<!-- stars:yuxino/kiri -->498<!-- /stars -->
<!-- stars:yuxino/WeChat -->9<!-- /stars -->
<!-- stars-updated -->2026-09-24<!-- /stars-updated -->
"""


class StarUpdateTests(unittest.TestCase):
    def test_counts_date_and_other_text(self):
        with patch.object(updater, "fetch_stars", side_effect=[1234, 0]):
            result = updater.refresh(SAMPLE, "2026-09-25")
        self.assertEqual(result, SAMPLE.replace("498", "1,234").replace(">9<", ">0<").replace("2026-09-24", "2026-09-25"))

    def test_same_snapshot_is_idempotent(self):
        with patch.object(updater, "fetch_stars", side_effect=[498, 9]):
            self.assertEqual(updater.refresh(SAMPLE, "2026-09-24"), SAMPLE)

    def test_malformed_and_duplicate_markers(self):
        variants = [SAMPLE + "<!-- stars:yuxino/kiri -->1<!-- /stars -->", SAMPLE.replace("-->498", "-->unknown"), SAMPLE.replace("<!-- stars-updated -->", ""), SAMPLE + "<!-- stars-updated -->bad<!-- /stars-updated -->"]
        for text in variants:
            with self.subTest(text=text), self.assertRaises(ValueError):
                updater.refresh(text, "2026-09-25")

    def test_failed_request_leaves_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(SAMPLE, encoding="utf-8")
            with patch.object(updater, "README", readme), patch.object(updater, "fetch_stars", side_effect=[500, RuntimeError("API unavailable")]):
                with self.assertRaises(RuntimeError):
                    updater.main()
            self.assertEqual(readme.read_text(encoding="utf-8"), SAMPLE)

    def test_api_reads_only_repository_metadata(self):
        body = b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}'
        with patch.object(updater, "urlopen", return_value=io.BytesIO(body)) as request:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        self.assertEqual(request.call_args.args[0].full_url, "https://api.github.com/repos/yuxino/kiri")

    def test_invalid_api_values_are_not_written_as_zero(self):
        bodies = [b'{"full_name":"yuxino/kiri","private":false}', b'{"full_name":"yuxino/kiri","private":true,"stargazers_count":5}', b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":true}', b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":-1}']
        for body in bodies:
            with self.subTest(body=body), patch.object(updater, "urlopen", return_value=io.BytesIO(body)), self.assertRaises(ValueError):
                updater.fetch_stars("yuxino/kiri")

    def test_transient_failure_is_retried(self):
        error = HTTPError("https://api.github.com/repos/yuxino/kiri", 503, "Unavailable", {}, None)
        body = io.BytesIO(b'{"full_name":"yuxino/kiri","private":false,"stargazers_count":498}')
        with patch.object(updater, "urlopen", side_effect=[error, body]), patch.object(updater.time, "sleep") as sleep:
            self.assertEqual(updater.fetch_stars("yuxino/kiri"), 498)
        sleep.assert_called_once_with(1)

    def test_profile_has_fifteen_unique_projects_and_no_images(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(len(updater.STARS.findall(text)), 15)
        self.assertEqual(text.count("<details>"), 1)
        self.assertNotIn("<img", text)
        self.assertNotIn("![", text)
        with patch.object(updater, "fetch_stars", return_value=1):
            updater.refresh(text, "2026-09-25")


if __name__ == "__main__":
    unittest.main()
