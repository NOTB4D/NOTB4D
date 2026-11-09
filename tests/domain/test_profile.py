import unittest
from datetime import date

from profile_card.domain.profile import StaticEntry, UptimeEntry


class ProfileEntryTests(unittest.TestCase):
    def test_static_entry_value_does_not_depend_on_the_day(self):
        entry = StaticEntry(key="Host", value="Mobven")

        self.assertEqual(entry.value_on(date(2026, 11, 9)), "Mobven")

    def test_uptime_entry_value_is_the_time_elapsed_since_its_start(self):
        entry = UptimeEntry(key="Uptime", since=date(2020, 12, 12))

        self.assertEqual(entry.value_on(date(2026, 11, 9)), "5 years, 10 months, 28 days")


if __name__ == "__main__":
    unittest.main()
