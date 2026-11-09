import unittest
from datetime import date

from profile_card.domain.elapsed import Elapsed, elapsed_between


class ElapsedBetweenTests(unittest.TestCase):
    def test_counts_whole_years_months_and_remaining_days(self):
        self.assertEqual(
            elapsed_between(date(2020, 12, 12), date(2026, 11, 9)),
            Elapsed(years=5, months=10, days=28),
        )

    def test_same_day_is_zero(self):
        self.assertEqual(elapsed_between(date(2024, 5, 1), date(2024, 5, 1)), Elapsed(0, 0, 0))

    def test_clips_to_the_last_day_of_a_shorter_month(self):
        self.assertEqual(elapsed_between(date(2024, 1, 31), date(2024, 3, 1)), Elapsed(0, 1, 1))

    def test_leap_day_start_completes_a_year_on_february_28th(self):
        self.assertEqual(elapsed_between(date(2020, 2, 29), date(2021, 2, 28)), Elapsed(1, 0, 0))

    def test_rejects_an_end_before_the_start(self):
        with self.assertRaises(ValueError):
            elapsed_between(date(2024, 5, 2), date(2024, 5, 1))


class ElapsedFormattingTests(unittest.TestCase):
    def test_uses_plural_units(self):
        self.assertEqual(str(Elapsed(5, 10, 28)), "5 years, 10 months, 28 days")

    def test_uses_singular_units_for_one(self):
        self.assertEqual(str(Elapsed(1, 1, 1)), "1 year, 1 month, 1 day")

    def test_uses_plural_units_for_zero(self):
        self.assertEqual(str(Elapsed(0, 0, 0)), "0 years, 0 months, 0 days")


if __name__ == "__main__":
    unittest.main()
