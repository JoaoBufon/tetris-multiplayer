from __future__ import annotations

import argparse
from queue import Empty
import socket
import sys
import time

import pygame

from tetris.board import Board
from tetris.constants import BOARD_HEIGHT, BOARD_WIDTH, COLORS
from tetris.game import Game
from tetris.network import NetworkClient
from tetris.pieces import Piece
from tetris.protocol import split_message


WINDOW_WIDTH = 980
WINDOW_HEIGHT = 720
LOCAL_CELL = 30
REMOTE_CELL = 20
LOCAL_ORIGIN = (70, 72)
REMOTE_ORIGIN = (520, 142)
BACKGROUND = (14, 17, 24)
PANEL = (28, 32, 43)
TEXT = (235, 238, 245)
MUTED = (155, 162, 177)
GRID = (48, 53, 67)


class TetrisClientApp:
    def __init__(self, host: str, port: int, name: str):
        pygame.init()
        pygame.display.set_caption("Tetris TCP — Dois jogadores")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.title_font = pygame.font.SysFont("arial", 30, bold=True)
        self.font = pygame.font.SysFont("arial", 22)
        self.small_font = pygame.font.SysFont("arial", 17)
        self.name = name
        self.network = NetworkClient(host, port, name)
        self.game: Game | None = None
        self.opponent_board = [[0] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]
        self.opponent_name = "Adversário"
        self.status = "Conectado. Aguardando outro jogador..."
        self.result: str | None = None
        self.running = True
        self.last_fall = time.monotonic()
        self.last_board_send = 0.0
        self.game_over_sent = False
        pygame.key.set_repeat(145, 45)

    def run(self) -> None:
        try:
            while self.running:
                delta = self.clock.tick(60) / 1000.0
                self._handle_network_events()
                self._handle_input()
                self._update(delta)
                self._draw()
        finally:
            self.network.close()
            pygame.quit()

    def _handle_network_events(self) -> None:
        while True:
            try:
                message = self.network.events.get_nowait()
            except Empty:
                break

            command, arguments = split_message(message)
            try:
                if command == "WAITING":
                    self.status = "Aguardando o segundo jogador..."
                elif command == "START" and len(arguments) >= 2:
                    self.game = Game(int(arguments[0]))
                    self.opponent_name = arguments[2] if len(arguments) >= 3 else "Adversário"
                    self.status = "Partida em andamento"
                    self.last_fall = time.monotonic()
                elif command == "GARBAGE" and arguments and self.game:
                    holes = [int(value) for value in arguments[0].split(",") if value]
                    self.game.queue_garbage(holes)
                elif command == "BOARD" and arguments:
                    self.opponent_board = Board.decode(arguments[0])
                elif command == "WIN":
                    self.result = "VOCÊ VENCEU!"
                    self.status = "Partida encerrada"
                elif command == "LOSE":
                    self.result = "VOCÊ PERDEU"
                    self.status = "Partida encerrada"
                elif command in ("DISCONNECT", "ERROR"):
                    if not self.result:
                        self.result = "CONEXÃO ENCERRADA"
                    self.status = arguments[0] if arguments else "Servidor desconectado"
            except (ValueError, IndexError):
                self.status = "O servidor enviou uma mensagem inválida"

    def _handle_input(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif self.game and not self.game.game_over and not self.result:
                    self._game_key(event.key)

    def _game_key(self, key: int) -> None:
        assert self.game is not None
        if key in (pygame.K_LEFT, pygame.K_a):
            self.game.move(-1, 0)
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.game.move(1, 0)
        elif key in (pygame.K_DOWN, pygame.K_s):
            locked, _, attack = self.game.step_down(soft_drop=True)
            if locked:
                self._after_lock(attack)
        elif key in (pygame.K_UP, pygame.K_x):
            self.game.rotate(1)
        elif key == pygame.K_z:
            self.game.rotate(-1)
        elif key == pygame.K_SPACE:
            _, attack = self.game.hard_drop()
            self._after_lock(attack)

    def _update(self, _delta: float) -> None:
        if not self.game or self.result:
            return

        now = time.monotonic()
        if now - self.last_fall >= self.game.gravity_interval:
            locked, _, attack = self.game.step_down()
            self.last_fall = now
            if locked:
                self._after_lock(attack)

        if self.game.game_over and not self.game_over_sent:
            self.game_over_sent = True
            self.network.send("GAME_OVER")
            self.status = "Game over — aguardando confirmação..."

        if now - self.last_board_send >= 0.1:
            self.network.send(f"BOARD|{self.game.board.encode(self.game.current)}")
            self.last_board_send = now

    def _after_lock(self, attack: int) -> None:
        self.last_fall = time.monotonic()
        if attack:
            self.network.send(f"ATTACK|{attack}")

    def _draw(self) -> None:
        self.screen.fill(BACKGROUND)
        self.screen.blit(self.title_font.render("TETRIS TCP", True, TEXT), (68, 24))
        self.screen.blit(self.small_font.render(self.status, True, MUTED), (520, 82))

        self._draw_panel((48, 58, 344, 624))
        self._draw_panel((493, 122, 244, 444))
        local_grid = self.game.board.snapshot(self.game.current) if self.game else [[0] * 10 for _ in range(20)]
        self._draw_board(local_grid, LOCAL_ORIGIN, LOCAL_CELL)
        self._draw_board(self.opponent_board, REMOTE_ORIGIN, REMOTE_CELL)

        self.screen.blit(self.font.render(self.name, True, TEXT), (70, 650))
        self.screen.blit(self.font.render(self.opponent_name, True, TEXT), (520, 112))

        if self.game:
            self._draw_stats()
        else:
            self._draw_waiting()

        if self.result:
            self._draw_result()
        pygame.display.flip()

    def _draw_panel(self, rect: tuple[int, int, int, int]) -> None:
        pygame.draw.rect(self.screen, PANEL, rect, border_radius=10)

    def _draw_board(self, grid: list[list[int]], origin: tuple[int, int], cell: int) -> None:
        ox, oy = origin
        for y, row in enumerate(grid):
            for x, value in enumerate(row):
                rect = pygame.Rect(ox + x * cell, oy + y * cell, cell, cell)
                pygame.draw.rect(self.screen, COLORS[value], rect)
                pygame.draw.rect(self.screen, GRID, rect, 1)
                if value:
                    highlight = pygame.Rect(rect.x + 3, rect.y + 3, max(2, cell - 6), 3)
                    pygame.draw.rect(self.screen, tuple(min(255, c + 35) for c in COLORS[value]), highlight)

    def _draw_stats(self) -> None:
        assert self.game is not None
        x = 780
        labels = (
            ("Pontos", str(self.game.score)),
            ("Linhas", str(self.game.total_lines)),
            ("Nível", str(self.game.level)),
            ("Lixo pendente", str(len(self.game.pending_garbage))),
        )
        y = 145
        for label, value in labels:
            self.screen.blit(self.small_font.render(label, True, MUTED), (x, y))
            self.screen.blit(self.font.render(value, True, TEXT), (x, y + 23))
            y += 70

        self.screen.blit(self.small_font.render("Próxima peça", True, MUTED), (x, y + 4))
        preview = Piece(self.game.next_kind, x=0, y=0)
        color = COLORS[{"I": 1, "J": 2, "L": 3, "O": 4, "S": 5, "T": 6, "Z": 7}[preview.kind]]
        for px, py in preview.cells():
            rect = pygame.Rect(x + px * 22, y + 38 + py * 22, 22, 22)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, GRID, rect, 1)

        controls = ("← → mover", "↑ / X girar", "Z giro inverso", "↓ queda suave", "Espaço hard drop")
        y = 535
        for text in controls:
            self.screen.blit(self.small_font.render(text, True, MUTED), (780, y))
            y += 27

    def _draw_waiting(self) -> None:
        text = self.font.render("O jogo inicia quando 2 jogadores conectarem.", True, TEXT)
        self.screen.blit(text, (485, 605))

    def _draw_result(self) -> None:
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        self.screen.blit(overlay, (0, 0))
        text = self.title_font.render(self.result, True, (255, 255, 255))
        subtext = self.font.render("Pressione Esc para sair", True, (220, 220, 220))
        self.screen.blit(text, text.get_rect(center=(WINDOW_WIDTH // 2, 315)))
        self.screen.blit(subtext, subtext.get_rect(center=(WINDOW_WIDTH // 2, 360)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cliente do Tetris multiplayer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--name", default="Jogador")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        TetrisClientApp(arguments.host, arguments.port, arguments.name).run()
    except (ConnectionRefusedError, socket.timeout, OSError) as error:
        print(f"Não foi possível conectar ao servidor: {error}")
        sys.exit(1)

