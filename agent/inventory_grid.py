"""Geometry for the visible first-screen alchemy inventory grid."""

from dataclasses import dataclass
from typing import Iterable


Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class GridPosition:
    """A zero-based row and column within an inventory grid."""

    row: int
    column: int

    def __post_init__(self) -> None:
        if self.row < 0 or self.column < 0:
            raise ValueError("row and column must be non-negative")


@dataclass(frozen=True)
class InventoryGrid:
    """Screen-space geometry for a rectangular inventory grid."""

    origin_x: int = 844
    origin_y: int = 153
    columns: int = 4
    rows: int = 5
    cell_width: int = 90
    cell_height: int = 90
    pitch_x: int = 97
    pitch_y: int = 97
    quantity_offset: Box = (50, 55, 40, 35)
    safe_click_offset: Box = (33, 28, 24, 24)

    def position_for_point(self, x: int | float, y: int | float) -> GridPosition:
        """Return the cell containing a point, excluding inter-cell pitch gaps."""
        column = int((x - self.origin_x) // self.pitch_x)
        row = int((y - self.origin_y) // self.pitch_y)
        if not (0 <= row < self.rows and 0 <= column < self.columns):
            raise ValueError("point is outside visible inventory")
        position = GridPosition(row=row, column=column)

        cell_x, cell_y, _, _ = self.cell_box(position)
        if not (cell_x <= x < cell_x + self.cell_width and cell_y <= y < cell_y + self.cell_height):
            raise ValueError("point is outside visible inventory")
        return position

    def position_for_box(self, box: Iterable[int | float]) -> GridPosition:
        """Return the grid cell containing the centre of a screen-space box."""
        x, y, width, height = box
        return self.position_for_point(x + width / 2, y + height / 2)

    def cell_box(self, position: GridPosition) -> Box:
        """Return the screen-space bounds of a grid cell."""
        self._validate_position(position)
        return (
            self.origin_x + position.column * self.pitch_x,
            self.origin_y + position.row * self.pitch_y,
            self.cell_width,
            self.cell_height,
        )

    def quantity_box(self, position: GridPosition) -> Box:
        """Return the quantity-recognition region within a grid cell."""
        return self._offset_box(position, self.quantity_offset)

    def safe_click_box(self, position: GridPosition) -> Box:
        """Return a conservative click target within a grid cell."""
        return self._offset_box(position, self.safe_click_offset)

    def _offset_box(self, position: GridPosition, offset: Box) -> Box:
        cell_x, cell_y, _, _ = self.cell_box(position)
        offset_x, offset_y, width, height = offset
        return (cell_x + offset_x, cell_y + offset_y, width, height)

    def _validate_position(self, position: GridPosition) -> None:
        if not self._contains(position):
            raise ValueError("position is outside visible inventory")

    def _contains(self, position: GridPosition) -> bool:
        return 0 <= position.row < self.rows and 0 <= position.column < self.columns


INVENTORY_GRID = InventoryGrid()
