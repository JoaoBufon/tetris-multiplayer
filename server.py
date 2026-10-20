from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import random
import socket
import threading

from tetris.board import Board
from tetris.constants import BOARD_WIDTH
from tetris.protocol import LineSocket, split_message


@dataclass
class Player:
    connection: LineSocket
    address: tuple[str, int]
    name: str = "Jogador"


@dataclass
class Match:
    first: Player
    second: Player
    seed: int = field(default_factory=lambda: random.SystemRandom().randrange(2**63))

    def __post_init__(self) -> None:
        self.players = (self.first, self.second)
        self._rng = random.SystemRandom()
        self._finish_lock = threading.Lock()
        self._finished = False

    def start(self) -> None:
        print(
            f"Partida iniciada: {self.first.address} x {self.second.address} "
            f"(seed {self.seed})"
        )
        self.first.connection.send(f"START|{self.seed}|1|{self.second.name}")
        self.second.connection.send(f"START|{self.seed}|2|{self.first.name}")

        threads = [
            threading.Thread(target=self._player_loop, args=(index,), daemon=True)
            for index in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        for player in self.players:
            player.connection.close()
        print("Partida encerrada")

    def _player_loop(self, index: int) -> None:
        player = self.players[index]
        try:
            while not self._finished:
                message = player.connection.receive()
                if message is None:
                    self._finish(index, disconnected=True)
                    return
                if not self._handle(index, message):
                    return
        except (OSError, UnicodeError, ValueError) as error:
            print(f"Erro com {player.address}: {error}")
            self._finish(index, disconnected=True)

    def _handle(self, index: int, message: str) -> bool:
        command, arguments = split_message(message)
        opponent = self.players[1 - index]

        if command == "ATTACK" and len(arguments) == 1:
            amount = int(arguments[0])
            if amount not in (1, 2, 4):
                raise ValueError("Ataque inválido")
            holes = [self._rng.randrange(BOARD_WIDTH) for _ in range(amount)]
            opponent.connection.send("GARBAGE|" + ",".join(map(str, holes)))
        elif command == "BOARD" and len(arguments) == 1:
            Board.decode(arguments[0])  # valida antes de retransmitir
            opponent.connection.send(f"BOARD|{arguments[0]}")
        elif command == "GAME_OVER":
            self._finish(index, disconnected=False)
            return False
        elif command == "DISCONNECT":
            self._finish(index, disconnected=True)
            return False
        elif command == "PING":
            self.players[index].connection.send("PONG")
        # Mensagens desconhecidas são ignoradas, sem derrubar a partida.
        return True

    def _finish(self, loser_index: int, *, disconnected: bool) -> None:
        with self._finish_lock:
            if self._finished:
                return
            self._finished = True
            reason = "OPPONENT_DISCONNECTED" if disconnected else "GAME_OVER"
            try:
                self.players[loser_index].connection.send(f"LOSE|{reason}")
            except OSError:
                pass
            try:
                self.players[1 - loser_index].connection.send(f"WIN|{reason}")
            except OSError:
                pass


class TetrisServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            print(f"Servidor ouvindo em {self.host}:{self.port}")
            waiting: Player | None = None

            while True:
                raw_socket, address = server.accept()
                raw_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                connection = LineSocket(raw_socket)
                try:
                    hello = connection.receive()
                    command, arguments = split_message(hello or "")
                    if command != "HELLO" or len(arguments) != 1:
                        raise ValueError("Handshake inválido")
                    name = arguments[0][:24] or "Jogador"
                    player = Player(connection, address, name)
                    print(f"Conectado: {name} em {address}")

                    if waiting is None:
                        waiting = player
                        connection.send("WAITING")
                    else:
                        match = Match(waiting, player)
                        waiting = None
                        threading.Thread(target=match.start, daemon=True).start()
                except (OSError, UnicodeError, ValueError) as error:
                    print(f"Conexão rejeitada de {address}: {error}")
                    connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servidor do Tetris multiplayer")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        TetrisServer(arguments.host, arguments.port).serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado")

