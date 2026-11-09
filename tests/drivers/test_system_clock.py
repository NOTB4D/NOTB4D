import unittest
from datetime import date, datetime, timedelta, timezone

from profile_card.drivers.system_clock import SystemClock


class SystemClockTests(unittest.TestCase):
    def test_today_is_the_utc_calendar_day(self):
        late_evening_in_utc = datetime(2026, 11, 9, 23, 30, tzinfo=timezone.utc)

        self.assertEqual(SystemClock(now=lambda: late_evening_in_utc).today(), date(2026, 11, 9))

    def test_reads_the_real_clock_by_default(self):
        today = SystemClock().today()

        self.assertLessEqual(abs(today - datetime.now(timezone.utc).date()), timedelta(days=1))


if __name__ == "__main__":
    unittest.main()
