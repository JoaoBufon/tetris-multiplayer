from __future__ import annotations

from dataclasses import dataclass
import random


SHAPES: dict[str, tuple[tuple[str, ...], ...]] = {
    "I": (
        ("....", "XXXX", "....", "...."),
        ("..X.", "..X.", "..X.", "..X."),
    ),
    "J": (
        ("X..", "XXX", "..."),
        (".XX", ".X.", ".X."),
        ("...", "XXX", "..X"),
        (".X.", ".X.", "XX."),
    ),
    "L": (
        ("..X", "XXX", "..."),
        (".X.", ".X.", ".XX"),
        ("...", "XXX", "X.."),
        ("XX.", ".X.", ".X."),
    ),
    "O": ((".XX", ".XX", "..."),),
    "S": (
        (".XX", "XX.", "..."),
        (".X.", ".XX", "..X"),
    ),
    "T": (
        (".X.", "XXX", "..."),
        (".X.", ".XX", ".X."),
        ("...", "XXX", ".X."),
        (".X.", "XX.", ".X."),
    ),
    "Z": (
        ("XX.", ".XX", "..."),
        ("..X", ".XX", ".X."),
    ),
}


@dataclass
class Piece:
    kind: str
    x: int = 3
    y: int = -1
    rotation: int = 0

    def cells(self, *, rotation: int | None = None, x: int | None = None,
              y: int | None = None) -> list[tuple[int, int]]:
        selected_rotation = self.rotation if rotation is None else rotation
        selected_x = self.x if x is None else x
        selected_y = self.y if y is None else y
        shape = SHAPES[self.kind][selected_rotation % len(SHAPES[self.kind])]
        return [
            (selected_x + column, selected_y + row)
            for row, line in enumerate(shape)
            for column, cell in enumerate(line)
            if cell == "X"
        ]

    @property
    def rotation_count(self) -> int:
        return len(SHAPES[self.kind])


class PieceGenerator:
    """Gerador 7-bag determinístico e independente de outros aleatórios."""

    def __init__(self, seed: int):
        self._random = random.Random(seed)
        self._bag: list[str] = []

    def next_kind(self) -> str:
        if not self._bag:
            self._bag = list(SHAPES)
            self._random.shuffle(self._bag)
        return self._bag.pop()

