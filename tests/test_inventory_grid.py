import pytest

from agent.inventory_grid import GridPosition, INVENTORY_GRID


@pytest.mark.parametrize(
    ("point", "expected"),
    [((889, 198), GridPosition(row=0, column=0)), ((1180, 489), GridPosition(row=3, column=3))],
)
def test_position_for_point_maps_cell_centres(
    point: tuple[int, int], expected: GridPosition
) -> None:
    assert INVENTORY_GRID.position_for_point(*point) == expected


@pytest.mark.parametrize("point", [(843, 153), (1233, 153), (844, 638)])
def test_position_for_point_rejects_points_outside_visible_grid(point: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match="outside visible inventory"):
        INVENTORY_GRID.position_for_point(*point)


@pytest.mark.parametrize("point", [(934, 198), (889, 243)])
def test_position_for_point_rejects_pitch_gaps(point: tuple[int, int]) -> None:
    with pytest.raises(ValueError, match="outside visible inventory"):
        INVENTORY_GRID.position_for_point(*point)


def test_position_for_box_maps_its_centre() -> None:
    assert INVENTORY_GRID.position_for_box((1135, 444, 90, 90)) == GridPosition(row=3, column=3)


def test_quantity_box_is_inside_bottom_right_half_of_its_cell() -> None:
    position = GridPosition(row=1, column=2)
    cell_x, cell_y, cell_width, cell_height = INVENTORY_GRID.cell_box(position)
    x, y, width, height = INVENTORY_GRID.quantity_box(position)

    assert cell_x + cell_width // 2 <= x < cell_x + cell_width
    assert cell_y + cell_height // 2 <= y < cell_y + cell_height
    assert x + width <= cell_x + cell_width
    assert y + height <= cell_y + cell_height


def test_safe_click_box_is_inside_cell_and_at_least_twenty_pixels_from_each_edge() -> None:
    position = GridPosition(row=4, column=3)
    cell_x, cell_y, cell_width, cell_height = INVENTORY_GRID.cell_box(position)
    x, y, width, height = INVENTORY_GRID.safe_click_box(position)

    assert cell_x + 20 <= x
    assert cell_y + 20 <= y
    assert x + width <= cell_x + cell_width - 20
    assert y + height <= cell_y + cell_height - 20


@pytest.mark.parametrize("position", [GridPosition(row=5, column=0), GridPosition(row=0, column=4)])
@pytest.mark.parametrize("box_helper", ["cell_box", "quantity_box", "safe_click_box"])
def test_box_helpers_reject_out_of_bounds_position(position: GridPosition, box_helper: str) -> None:
    with pytest.raises(ValueError, match="outside visible inventory"):
        getattr(INVENTORY_GRID, box_helper)(position)
