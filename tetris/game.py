from __future__ import annotations

from collections import deque

from .board import Board
from .constants import ATTACK_TABLE
from .pieces import Piece, PieceGenerator


class Game:
    def __init__(self, seed: int):
        self.board = Board()
        self.generator = PieceGenerator(seed)
        self.current = Piece(self.generator.next_kind())
        self.next_kind = self.generator.next_kind()
        self.pending_garbage: deque[int] = deque()
        self.score = 0
        self.total_lines = 0
        self.level = 1
        self.game_over = not self.board.can_place(self.current)

    @property
    def gravity_interval(self) -> float:
        return max(0.08, 0.72 - (self.level - 1) * 0.055)

    def move(self, dx: int, dy: int) -> bool:
        new_x = self.current.x + dx
        new_y = self.current.y + dy
        if self.board.can_place(self.current, x=new_x, y=new_y):
            self.current.x = new_x
            self.current.y = new_y
            return True
        return False

    def rotate(self, direction: int = 1) -> bool:
        target = (self.current.rotation + direction) % self.current.rotation_count
        # Pequeno wall kick suficiente para uma implementação acadêmica.
        for offset_x, offset_y in ((0, 0), (-1, 0), (1, 0), (-2, 0), (2, 0), (0, -1)):
            if self.board.can_place(
                self.current,
                x=self.current.x + offset_x,
                y=self.current.y + offset_y,
                rotation=target,
            ):
                self.current.rotation = target
                self.current.x += offset_x
                self.current.y += offset_y
                return True
        return False

    def hard_drop(self) -> tuple[int, int]:
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        return self.lock_current()

    def step_down(self, *, soft_drop: bool = False) -> tuple[bool, int, int]:
        if self.move(0, 1):
            if soft_drop:
                self.score += 1
            return False, 0, 0
        cleared, attack = self.lock_current()
        return True, cleared, attack

    def queue_garbage(self, holes: list[int]) -> None:
        self.pending_garbage.extend(holes)

    def lock_current(self) -> tuple[int, int]:
        if not self.board.lock(self.current):
            self.game_over = True
            return 0, 0

        cleared = self.board.clear_full_lines()
        attack = ATTACK_TABLE.get(cleared, 0)
        self.total_lines += cleared
        self.level = 1 + self.total_lines // 10
        self.score += {0: 0, 1: 100, 2: 300, 3: 500, 4: 800}[cleared] * self.level

        # O lixo recebido durante a queda entra somente entre duas peças.
        holes = list(self.pending_garbage)
        self.pending_garbage.clear()
        if holes and self.board.add_garbage(holes):
            self.game_over = True

        self.current = Piece(self.next_kind)
        self.next_kind = self.generator.next_kind()
        if not self.board.can_place(self.current):
            self.game_over = True
        return cleared, attack

