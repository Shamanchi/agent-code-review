"""Самообучение: веса правил на основе accept/reject фидбека."""

from __future__ import annotations


class EvolutionStore:
    """In-memory хранилище весов. Accept повышает, reject понижает (с границами)."""

    def __init__(
        self,
        min_weight: float = 0.1,
        max_weight: float = 2.0,
        upvote_step: float = 0.1,
        downvote_step: float = 0.2,
    ) -> None:
        self._min = min_weight
        self._max = max_weight
        self._up = upvote_step
        self._down = downvote_step
        self._weights: dict[str, float] = {}

    def weight(self, rule: str) -> float:
        return self._weights.get(rule, 1.0)

    def weights(self) -> dict[str, float]:
        return dict(self._weights)

    def feedback(self, rule: str, accepted: bool) -> float:
        current = self.weight(rule)
        updated = current + self._up if accepted else current - self._down
        updated = max(self._min, min(self._max, updated))
        self._weights[rule] = round(updated, 2)
        return self._weights[rule]

    def reset(self) -> None:
        self._weights.clear()


_store: EvolutionStore | None = None


def get_store(
    min_weight: float = 0.1,
    max_weight: float = 2.0,
    upvote_step: float = 0.1,
    downvote_step: float = 0.2,
) -> EvolutionStore:
    global _store
    if _store is None:
        _store = EvolutionStore(min_weight, max_weight, upvote_step, downvote_step)
    return _store
