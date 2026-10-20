import socket
import unittest

from tetris.protocol import LineSocket, split_message


class ProtocolTest(unittest.TestCase):
    def test_receive_handles_fragmented_and_grouped_messages(self):
        left, right = socket.socketpair()
        try:
            connection = LineSocket(left)
            right.sendall(b"ATT")
            right.sendall(b"ACK|4\nBOARD|123\n")
            self.assertEqual(connection.receive(), "ATTACK|4")
            self.assertEqual(connection.receive(), "BOARD|123")
        finally:
            left.close()
            right.close()

    def test_split_message(self):
        self.assertEqual(split_message("GARBAGE|2,7"), ("GARBAGE", ["2,7"]))


if __name__ == "__main__":
    unittest.main()

