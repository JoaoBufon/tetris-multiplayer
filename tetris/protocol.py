from __future__ import annotations

import socket
import threading


MAX_MESSAGE_BYTES = 8192


class LineSocket:
    """Mensagens UTF-8 delimitadas por linha sobre um socket TCP."""

    def __init__(self, sock: socket.socket):
        self.sock = sock
        self._buffer = bytearray()
        self._send_lock = threading.Lock()

    def send(self, message: str) -> None:
        if "\n" in message or "\r" in message:
            raise ValueError("A mensagem não pode conter quebra de linha")
        data = (message + "\n").encode("utf-8")
        if len(data) > MAX_MESSAGE_BYTES:
            raise ValueError("Mensagem grande demais")
        with self._send_lock:
            self.sock.sendall(data)

    def receive(self) -> str | None:
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                raw = bytes(self._buffer[:newline])
                del self._buffer[:newline + 1]
                return raw.rstrip(b"\r").decode("utf-8")

            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            self._buffer.extend(chunk)
            if len(self._buffer) > MAX_MESSAGE_BYTES:
                raise ValueError("Mensagem recebida excede o limite")

    def close(self) -> None:
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


def split_message(message: str) -> tuple[str, list[str]]:
    parts = message.split("|")
    return parts[0].upper(), parts[1:]

