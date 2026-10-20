from __future__ import annotations

from .constants import BOARD_HEIGHT, BOARD_WIDTH, EMPTY, GARBAGE, TYPE_TO_VALUE
from .pieces import Piece


class Board:
    def __init__(self):
        self.grid = [
            [EMPTY for _ in range(BOARD_WIDTH)]
            for _ in range(BOARD_HEIGHT)
        ]

    def can_place(self, piece: Piece, *, x: int | None = None,
                  y: int | None = None, rotation: int | None = None) -> bool:
        for cell_x, cell_y in piece.cells(x=x, y=y, rotation=rotation):
            if cell_x < 0 or cell_x >= BOARD_WIDTH or cell_y >= BOARD_HEIGHT:
                return False
            if cell_y >= 0 and self.grid[cell_y][cell_x] != EMPTY:
                return False
        return True

    def lock(self, piece: Piece) -> bool:
        """Fixa a peça. Retorna False se alguma célula ficou acima do topo."""
        cells = piece.cells()
        if any(y < 0 for _, y in cells):
            return False
        value = TYPE_TO_VALUE[piece.kind]
        for x, y in cells:
            self.grid[y][x] = value
        return True

    def clear_full_lines(self) -> int:
        remaining = [row for row in self.grid if any(cell == EMPTY for cell in row)]
        cleared = BOARD_HEIGHT - len(remaining)
        self.grid = [
            [EMPTY for _ in range(BOARD_WIDTH)] for _ in range(cleared)
        ] + remaining
        return cleared

    def add_garbage(self, holes: list[int]) -> bool:
        """Adiciona lixo e retorna True se blocos foram empurrados para fora."""
        overflow = False
        for hole in holes:
            if not 0 <= hole < BOARD_WIDTH:
                raise ValueError(f"Coluna de buraco inválida: {hole}")
            removed = self.grid.pop(0)
            overflow = overflow or any(cell != EMPTY for cell in removed)
            row = [GARBAGE for _ in range(BOARD_WIDTH)]
            row[hole] = EMPTY
            self.grid.append(row)
        return overflow

    def snapshot(self, piece: Piece | None = None) -> list[list[int]]:
        result = [row[:] for row in self.grid]
        if piece is not None:
            value = TYPE_TO_VALUE[piece.kind]
            for x, y in piece.cells():
                if 0 <= y < BOARD_HEIGHT and 0 <= x < BOARD_WIDTH:
                    result[y][x] = value
        return result

    def encode(self, piece: Piece | None = None) -> str:
        return "".join(str(cell) for row in self.snapshot(piece) for cell in row)

    @staticmethod
    def decode(payload: str) -> list[list[int]]:
        expected = BOARD_WIDTH * BOARD_HEIGHT
        if len(payload) != expected or any(char not in "012345678" for char in payload):
            raise ValueError("Snapshot de tabuleiro inválido")
        values = [int(char) for char in payload]
        return [
            values[index:index + BOARD_WIDTH]
            for index in range(0, expected, BOARD_WIDTH)
        ]

