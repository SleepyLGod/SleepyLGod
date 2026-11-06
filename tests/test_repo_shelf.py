"""Verify repository metadata scope, zero counts, and failure-safe publication."""

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


SPEC = importlib.util.spec_from_file_location("repo_shelf", Path(__file__).resolve().parents[1] / "scripts/build_repo_shelf.py")
shelf = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shelf)


class RepoShelfTests(unittest.TestCase):
    def repos(self):
        return [{"repo": "example/data", "description": "Changing data.", "category": "skills", "icon": "database"},
                {"repo": "example/compute", "description": "GPU kernels.", "category": "research", "icon": "chip"}]

    def closed_repo(self):
        return {"repo": "private/project", "description": "Scheduling under agentic workload",
                "category": "research", "icon": "chip", "public": False}

    def snapshot(self):
        return {"version": 1, "captured_at": "2026-11-06T03:00:00Z", "repositories": [
            {"repo": "example/data", "stars": 12345, "forks": 0, "source": "https://github.com/example/data"},
            {"repo": "example/compute", "stars": 12, "forks": 3, "source": "https://github.com/example/compute"}]}

    def test_counts_keep_exact_values_and_zero_forks(self):
        snapshot = self.snapshot()
        for theme in shelf.PALETTES:
            card = shelf.render_card(self.repos()[0], snapshot["repositories"][0], snapshot["captured_at"], theme)
            root = ET.fromstring(card)
            stars = next(e for e in root.iter() if e.get("class") == "repo-stars")
            forks = next(e for e in root.iter() if e.get("class") == "repo-forks")
            self.assertEqual((stars.text, forks.text), ("12,345", "0"))
            self.assertIn("Skills", card)
            self.assertIn("12345 Stars; 0 Forks", card)
            self.assertNotIn("<script", card)
            self.assertNotIn("<image", card)

    def test_snapshot_must_cover_exactly_the_configured_repositories(self):
        for transform in [lambda s: s["repositories"].pop(),
                          lambda s: s["repositories"].append(deepcopy(s["repositories"][0])),
                          lambda s: s["repositories"][0].update(stars=True)]:
            snapshot = self.snapshot()
            transform(snapshot)
            with self.assertRaises(ValueError):
                shelf.validate_stats(snapshot, self.repos())

    def test_private_or_renamed_repositories_are_not_published(self):
        for private, full_name in [(True, "example/data"), (False, "elsewhere/data")]:
            record = {"private": private, "full_name": full_name, "stargazers_count": 1, "forks_count": 0}
            with patch.object(shelf, "urlopen", return_value=io.BytesIO(json.dumps(record).encode())):
                with self.assertRaisesRegex(ValueError, "public repository"):
                    shelf.fetch_stats(self.repos()[:1], "test-token")

    def test_second_repository_fetch_failure_preserves_every_cached_file(self):
        record = {"private": False, "full_name": "example/data", "stargazers_count": 42, "forks_count": 0}
        error = HTTPError("https://api.github.com", 503, "Unavailable", {}, None)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            shelf.write_cards(output, self.repos(), self.snapshot())
            previous = {p.name: p.read_bytes() for p in output.iterdir()}
            with patch("sys.argv", ["build_repo_shelf.py", "--refresh", "--no-readme", "--output", directory]), \
                    patch.object(shelf, "load_repos", return_value=self.repos()), \
                    patch.object(shelf, "urlopen", side_effect=[io.BytesIO(json.dumps(record).encode()), error]):
                with self.assertRaisesRegex(RuntimeError, "503"):
                    shelf.main()
            self.assertEqual(previous, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_categories_preserve_native_links_to_each_repository(self):
        html = shelf.render_readme(self.repos(), "./assets/recommendations/")
        self.assertNotIn("<h4", html)
        self.assertLess(html.index("Research"), html.index("Skills"))
        for repo in self.repos():
            self.assertIn(f'<a href="https://github.com/{repo["repo"]}"><picture>', html)

    def test_failed_render_does_not_change_existing_cards_or_timestamp(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            shelf.write_cards(output, self.repos(), self.snapshot())
            previous = {p.name: p.read_bytes() for p in output.iterdir()}
            with patch.object(shelf, "render_card", side_effect=ValueError("invalid SVG")):
                with self.assertRaises(ValueError):
                    shelf.write_cards(output, self.repos(), self.snapshot())
            self.assertEqual(previous, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_closed_project_is_never_requested_from_github(self):
        public = self.repos()[0]
        response = {"private": False, "full_name": public["repo"], "stargazers_count": 2, "forks_count": 0}
        with patch.object(shelf, "urlopen", return_value=io.BytesIO(json.dumps(response).encode())) as request:
            snapshot = shelf.fetch_stats([self.closed_repo(), public], "test-token")
        self.assertEqual(request.call_count, 1)
        self.assertNotIn("private/project", request.call_args.args[0].full_url)
        self.assertEqual([r["repo"] for r in snapshot["repositories"]], [public["repo"]])

    def test_closed_project_has_no_link_or_invented_star_and_fork_counts(self):
        repo = self.closed_repo()
        for theme in shelf.PALETTES:
            content = shelf.render_card(repo, None, self.snapshot()["captured_at"], theme)
            root = ET.fromstring(content)
            self.assertIn("Not Yet Public", content)
            self.assertIn("Scheduling under agentic workload", content)
            self.assertFalse(any(e.get("class") in ("repo-stars", "repo-forks") for e in root.iter()))
        html = shelf.render_readme([repo], "./assets/recommendations/")
        self.assertNotIn("<a ", html)
        self.assertIn("<picture>", html)

    def test_closed_project_metadata_cannot_be_accidentally_published(self):
        repos = self.repos() + [self.closed_repo()]
        snapshot = self.snapshot()
        shelf.validate_stats(snapshot, repos)
        snapshot["repositories"].append({"repo": "private/project", "stars": 0, "forks": 0,
                                         "source": "https://github.com/private/project"})
        with self.assertRaises(ValueError):
            shelf.validate_stats(snapshot, repos)

    def test_closed_flag_must_be_an_explicit_boolean(self):
        repo = self.closed_repo()
        repo["public"] = "false"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "repos.json"
            source.write_text(json.dumps([repo]))
            with self.assertRaisesRegex(ValueError, "boolean"):
                shelf.load_repos(source)


if __name__ == "__main__":
    unittest.main()
