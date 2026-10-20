from __future__ import annotations

from queue import Queue
import socket
import threading

from .protocol import LineSocket


class NetworkClient:
    def __init__(self, host: str, port: int, player_name: str):
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.settimeout(8.0)
        raw_socket.connect((host, port))
        raw_socket.settimeout(None)
        raw_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.connection = LineSocket(raw_socket)
        self.events: Queue[str] = Queue()
        self._running = True
        self.connection.send(f"HELLO|{sanitize_name(player_name)}")
        self._thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._thread.start()

    def _receive_loop(self) -> None:
        try:
            while self._running:
                message = self.connection.receive()
                if message is None:
                    break
                self.events.put(message)
        except (OSError, UnicodeError, ValueError) as error:
            if self._running:
                self.events.put(f"ERROR|{error}")
        finally:
            if self._running:
                self.events.put("DISCONNECT")

    def send(self, message: str) -> None:
        if self._running:
            try:
                self.connection.send(message)
            except OSError:
                self.events.put("DISCONNECT")

    def close(self) -> None:
        if not self._running:
            return
        self._running = False
        try:
            self.connection.send("DISCONNECT")
        except OSError:
            pass
        self.connection.close()


def sanitize_name(name: str) -> str:
    clean = "".join(char for char in name.strip() if char.isprintable() and char not in "|\r\n")
    return clean[:24] or "Jogador"

