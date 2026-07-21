import pytest

from agent.selection import Candidate, SelectionError, select_best


def test_selects_single_candidate() -> None:
    candidate = Candidate(row=2, column=3, quantity=5, template_score=0.8)

    assert select_best([candidate]) == candidate


def test_selects_candidate_with_largest_quantity() -> None:
    smallest = Candidate(row=0, column=0, quantity=9, template_score=0.9)
    largest = Candidate(row=4, column=5, quantity=10, template_score=0.1)

    assert select_best([smallest, largest]) == largest


def test_quantity_tie_selects_earlier_row_major_candidate_regardless_of_template_score() -> None:
    earlier = Candidate(row=1, column=4, quantity=200, template_score=0.1)
    later = Candidate(row=2, column=0, quantity=200, template_score=0.99)

    assert select_best([later, earlier]) == earlier


def test_same_row_quantity_tie_selects_lower_column() -> None:
    later = Candidate(row=3, column=5, quantity=20, template_score=0.9)
    earlier = Candidate(row=3, column=2, quantity=20, template_score=0.1)

    assert select_best([later, earlier]) == earlier


def test_empty_candidates_raise_selection_error() -> None:
    with pytest.raises(SelectionError, match="no valid candidates"):
        select_best([])


@pytest.mark.parametrize(("row", "column"), [(-1, 0), (0, -1)])
def test_negative_row_or_column_is_rejected(row: int, column: int) -> None:
    with pytest.raises(ValueError, match="row and column must be non-negative"):
        Candidate(row=row, column=column, quantity=1, template_score=0.0)


@pytest.mark.parametrize("quantity", [0, -1])
def test_non_positive_quantity_is_rejected(quantity: int) -> None:
    with pytest.raises(ValueError, match="quantity must be positive"):
        Candidate(row=0, column=0, quantity=quantity, template_score=0.0)
