import unittest

from profile_card.application.refresh_card import RefreshProfileCard
from profile_card.domain.card import compose_card
from tests.domain.test_card import CONTENT, STATS, TODAY


class FixedClock:
    def today(self):
        return TODAY


class StubStatsCollector:
    def __init__(self, stats):
        self._stats = stats
        self.logins: list[str] = []

    def collect(self, login):
        self.logins.append(login)
        return self._stats


class RecordingPublisher:
    def __init__(self):
        self.cards = []

    def publish(self, card):
        self.cards.append(card)


class RefreshProfileCardTests(unittest.TestCase):
    def setUp(self):
        self.collector = StubStatsCollector(STATS)
        self.publisher = RecordingPublisher()
        self.use_case = RefreshProfileCard(
            stats=self.collector, content=CONTENT, clock=FixedClock(), publisher=self.publisher
        )

    def test_publishes_the_card_composed_from_todays_stats(self):
        self.use_case.execute("NOTB4D")

        self.assertEqual(self.publisher.cards, [compose_card(CONTENT, STATS, TODAY)])

    def test_collects_stats_of_the_given_login(self):
        self.use_case.execute("NOTB4D")

        self.assertEqual(self.collector.logins, ["NOTB4D"])


if __name__ == "__main__":
    unittest.main()
