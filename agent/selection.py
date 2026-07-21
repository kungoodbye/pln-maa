from dataclasses import dataclass


class SelectionError(RuntimeError):
    """Raised when no visible inventory stack can be selected."""


@dataclass(frozen=True)
class Candidate:
    row: int
    column: int
    quantity: int
    template_score: float

    def __post_init__(self) -> None:
        if self.row < 0 or self.column < 0:
            raise ValueError("row and column must be non-negative")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")


def select_best(candidates: list[Candidate]) -> Candidate:
    """Select the largest stack, breaking quantity ties by row-major position."""
    if not candidates:
        raise SelectionError("no valid candidates")

    return min(candidates, key=lambda candidate: (-candidate.quantity, candidate.row, candidate.column))
