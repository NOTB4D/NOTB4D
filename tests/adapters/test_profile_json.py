import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from profile_card.adapters.profile_json import load_profile_content
from profile_card.domain.profile import ProfileContent, StaticEntry, UptimeEntry


class LoadProfileContentTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.path = Path(self._directory.name) / "profile.json"

    def tearDown(self):
        self._directory.cleanup()

    def load(self, document):
        self.path.write_text(json.dumps(document), encoding="utf-8")
        return load_profile_content(self.path)

    def test_reads_the_title_about_groups_and_contact(self):
        content = self.load(
            {
                "title": "eser@kucuker",
                "about": [
                    [{"key": "OS", "value": "macOS, iOS"}, {"key": "Uptime", "since": "2020-12-12"}],
                    [{"key": "Languages.Real", "value": "Turkish, English"}],
                ],
                "contact": [{"key": "GitHub", "value": "NOTB4D"}],
            }
        )

        self.assertEqual(
            content,
            ProfileContent(
                title="eser@kucuker",
                about=(
                    (StaticEntry("OS", "macOS, iOS"), UptimeEntry("Uptime", date(2020, 12, 12))),
                    (StaticEntry("Languages.Real", "Turkish, English"),),
                ),
                contact=(StaticEntry("GitHub", "NOTB4D"),),
            ),
        )

    def test_contact_is_optional(self):
        content = self.load({"title": "eser@kucuker", "about": [[{"key": "OS", "value": "macOS"}]]})

        self.assertEqual(content.contact, ())

    def test_rejects_an_entry_without_value_or_since(self):
        with self.assertRaisesRegex(ValueError, "'OS'"):
            self.load({"title": "t", "about": [[{"key": "OS"}]]})

    def test_rejects_an_entry_with_both_value_and_since(self):
        with self.assertRaisesRegex(ValueError, "'Uptime'"):
            self.load({"title": "t", "about": [[{"key": "Uptime", "value": "x", "since": "2020-12-12"}]]})

    def test_rejects_an_invalid_since_date(self):
        with self.assertRaisesRegex(ValueError, "2020-13-12"):
            self.load({"title": "t", "about": [[{"key": "Uptime", "since": "2020-13-12"}]]})


if __name__ == "__main__":
    unittest.main()
