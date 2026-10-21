"""Checks for calendar correctness and preserving the last good profile snapshot."""

from datetime import date, timedelta
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


SPEC = importlib.util.spec_from_file_location(
    "profile_assets", Path(__file__).resolve().parents[1] / "scripts/update_profile.py")
profile = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(profile)


class ContributionTests(unittest.TestCase):
    def days(self, counts):
        start = date(2026, 1, 1)
        return [(start + timedelta(days=index), value) for index, value in enumerate(counts)]

    def test_counts_contributions_and_days_separately(self):
        self.assertEqual(profile.statistics(self.days([3, 0, 2, 4, 1])), (10, 4, 3, 3))

    def test_today_may_still_be_in_progress(self):
        self.assertEqual(profile.statistics(self.days([0, 2, 3, 0]))[-1], 2)

    def test_yesterday_without_contributions_ends_streak(self):
        self.assertEqual(profile.statistics(self.days([3, 2, 0, 0]))[-1], 0)

    def test_calendar_window_handles_leap_day(self):
        today = date(2024, 3, 1)
        start, _ = profile.period(today)
        raw = [{"date": str(start + timedelta(days=i)), "contributionCount": i % 4} for i in range(365)]
        days = profile.normalize_days(raw, today)
        self.assertEqual(len(days), 365)
        self.assertIn(date(2024, 2, 29), dict(days))
        with self.assertRaisesRegex(ValueError, "365"):
            profile.normalize_days(raw[:-1], today)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            profile.normalize_days(raw + raw[:1], today)

    def test_public_calendar_requires_exact_counts(self):
        parser = profile.PublicCalendarParser()
        parser.feed('<td data-date="2026-10-20" id="day-a"></td>'
                    '<tool-tip for="day-a">1,234 contributions on October 20th.</tool-tip>'
                    '<td data-date="2026-10-21" id="day-b"></td>'
                    '<tool-tip for="day-b">No contributions on October 21st.</tool-tip>')
        self.assertEqual([day["contributionCount"] for day in parser.days()], [1234, 0])
        parser.feed('<td data-date="2026-10-22" id="unknown"></td>')
        with self.assertRaisesRegex(ValueError, "incomplete"):
            parser.days()

    def test_all_cards_are_valid_svg(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            profile.write_cards(output, "SleepyLGod", self.days([0, 3, 2, 0]))
            files = sorted(output.glob("*.svg"))
            self.assertEqual(len(files), 4)
            for path in files:
                self.assertEqual(ET.parse(path).getroot().tag, "{http://www.w3.org/2000/svg}svg")
                self.assertNotIn("<script", path.read_text())

    def test_render_failure_preserves_previous_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            profile.write_cards(output, "SleepyLGod", self.days([0, 3, 2, 0]))
            previous = {path.name: path.read_bytes() for path in output.glob("*.svg")}
            with patch.object(profile, "calendar_svg", side_effect=ValueError("invalid source")):
                with self.assertRaises(ValueError):
                    profile.write_cards(output, "SleepyLGod", self.days([1, 2, 3, 4]))
            self.assertEqual(previous, {path.name: path.read_bytes() for path in output.glob("*.svg")})

    def test_api_failure_does_not_rewrite_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            profile.write_cards(output, "SleepyLGod", self.days([2, 0, 1, 0]))
            previous = {path.name: path.read_bytes() for path in output.glob("*.svg")}
            with patch("sys.argv", ["update_profile.py", "--output", str(output)]), \
                    patch.object(profile, "fetch_days", side_effect=RuntimeError("GitHub API failed")):
                with self.assertRaises(RuntimeError):
                    profile.main()
            self.assertEqual(previous, {path.name: path.read_bytes() for path in output.glob("*.svg")})


if __name__ == "__main__":
    unittest.main()
