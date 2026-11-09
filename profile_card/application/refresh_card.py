"""Refreshes the published profile card with today's numbers."""

from profile_card.application.ports import CardPublisher, Clock, StatsCollector
from profile_card.domain.card import compose_card
from profile_card.domain.profile import ProfileContent


class RefreshProfileCard:
    def __init__(
        self,
        stats: StatsCollector,
        content: ProfileContent,
        clock: Clock,
        publisher: CardPublisher,
    ):
        self._stats = stats
        self._content = content
        self._clock = clock
        self._publisher = publisher

    def execute(self, login: str) -> None:
        stats = self._stats.collect(login)
        self._publisher.publish(compose_card(self._content, stats, self._clock.today()))
