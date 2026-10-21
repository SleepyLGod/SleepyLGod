"""Public scope, pagination, truthful encodings, and last-good snapshot checks."""

from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
import xml.etree.ElementTree as ET


SPEC = importlib.util.spec_from_file_location(
    "code_atlas", Path(__file__).resolve().parents[1] / "scripts/update_code_atlas.py")
atlas = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(atlas)


class CodeAtlasTests(unittest.TestCase):
    def snapshot(self):
        return {"version": 1, "username": "SleepyLGod",
                "captured_at": "2026-10-20T23:30:00Z",
                "source": "https://github.com/SleepyLGod?tab=repositories&type=source",
                "repositories": [
                    {"name": name, "language": language, "stars": stars}
                    for name, language, stars in [
                        ("alpha", "Python", 3), ("beta", "Python", 2),
                        ("c-library", "C", 0), ("web", "HTML", 1),
                        ("notes", "TeX", 0), ("gateway", "Go", 0),
                        ("docs", None, 4)]]}

    def test_counts_primary_languages_and_every_repository_once(self):
        result = atlas.summarize(self.snapshot())
        self.assertEqual((result["repos"], result["stars"], result["languages"]), (7, 10, 5))
        self.assertEqual(sum(count for _, count in result["groups"]), 7)
        self.assertEqual(dict(result["groups"])["Unclassified"], 1)
        self.assertEqual(dict(result["groups"])["Other Languages"], 2)

    def test_api_reads_all_pages_and_excludes_private_and_forked_repos(self):
        def repo(index, **extra):
            return {"name": f"repo-{index}", "language": "Python", "stargazers_count": 1,
                    "fork": False, "private": False, "owner": {"login": "SleepyLGod"}, **extra}

        first = [repo(index) for index in range(100)]
        first[0]["fork"] = True
        first[1]["private"] = True
        second = [repo(100)]
        responses = [io.BytesIO(json.dumps(page).encode()) for page in (first, second)]
        with patch.object(atlas, "urlopen", side_effect=responses) as fetch:
            records = atlas.fetch_repositories("SleepyLGod", "test-token")
        self.assertEqual(len(records), 99)
        self.assertNotIn("repo-0", [record["name"] for record in records])
        self.assertNotIn("repo-1", [record["name"] for record in records])
        self.assertIn("repo-100", [record["name"] for record in records])
        self.assertIn("page=2", fetch.call_args_list[1].args[0].full_url)

    def test_incomplete_or_inconsistent_data_is_rejected(self):
        for field, value in (("stars", -1), ("stars", True), ("language", "")):
            snapshot = self.snapshot()
            snapshot["repositories"][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                atlas.validate_snapshot(snapshot)
        snapshot = self.snapshot()
        snapshot["repositories"].append(deepcopy(snapshot["repositories"][0]))
        snapshot["repositories"][-1]["name"] = "ALPHA"
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            atlas.validate_snapshot(snapshot)
        snapshot = self.snapshot()
        snapshot["captured_at"] = "2026-10-21T09:00:00"
        with self.assertRaisesRegex(ValueError, "timezone"):
            atlas.validate_snapshot(snapshot)

    def test_all_layouts_use_one_dot_per_repo_and_have_accessible_scope(self):
        snapshot = self.snapshot()
        for theme in atlas.PALETTES:
            for mobile in (False, True):
                with self.subTest(theme=theme, mobile=mobile):
                    content = atlas.render_card(snapshot, theme, mobile)
                    root = ET.fromstring(content)
                    dots = [element for element in root.iter() if element.get("class") == "repo-dot"]
                    self.assertEqual(len(dots), 7)
                    self.assertIn("7 public, non-fork repositories", content)
                    self.assertIn("10 stars earned, 5 primary languages", content)
                    self.assertIn("not code bytes or proficiency", content)
                    self.assertIn("Snapshot 2026-10-21", content)  # Hong Kong date.
                    self.assertNotIn("<script", content)
                    self.assertNotIn("<image", content)

    def test_empty_profile_renders_without_inventing_data(self):
        snapshot = self.snapshot()
        snapshot["repositories"] = []
        atlas.validate_snapshot(snapshot)
        content = atlas.render_card(snapshot, "dark")
        self.assertIn("0 public, non-fork repositories, 0 stars earned, 0 primary languages", content)
        self.assertNotIn('class="repo-dot"', content)
        ET.fromstring(content)

    def test_render_failure_preserves_all_previous_files(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            atlas.write_atlas(output, self.snapshot())
            previous = {path.name: path.read_bytes() for path in output.iterdir()}
            with patch.object(atlas, "render_card", side_effect=ValueError("invalid rendering")):
                with self.assertRaises(ValueError):
                    atlas.write_atlas(output, self.snapshot())
            self.assertEqual(previous, {path.name: path.read_bytes() for path in output.iterdir()})

    def test_api_failure_does_not_replace_previous_cards_or_date(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            atlas.write_atlas(output, self.snapshot())
            previous = {path.name: path.read_bytes() for path in output.iterdir()}
            error = HTTPError("https://api.github.com", 503, "Unavailable", {}, None)
            with patch("sys.argv", ["update_code_atlas.py", "--output", directory]), \
                    patch.object(atlas, "urlopen", side_effect=error):
                with self.assertRaisesRegex(RuntimeError, "503"):
                    atlas.main()
            self.assertEqual(previous, {path.name: path.read_bytes() for path in output.iterdir()})

    def test_offline_rebuild_preserves_observation_time(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = self.snapshot()
            source = Path(directory) / "source.json"
            source.write_text(json.dumps(snapshot))
            output = Path(directory) / "output"
            with patch("sys.argv", ["update_code_atlas.py", "--snapshot", str(source), "--output", str(output)]), \
                    patch.object(atlas, "fetch_repositories") as fetch:
                atlas.main()
            fetch.assert_not_called()
            self.assertEqual(json.loads((output / "code-atlas.json").read_text()), snapshot)
            self.assertEqual(len(list(output.glob("*.svg"))), 4)


if __name__ == "__main__":
    unittest.main()
