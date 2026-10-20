import unittest

from tetris.board import Board
from tetris.constants import BOARD_HEIGHT, BOARD_WIDTH, GARBAGE
from tetris.pieces import Piece


class BoardTest(unittest.TestCase):
    def test_clear_two_lines(self):
        board = Board()
        board.grid[-1] = [1] * BOARD_WIDTH
        board.grid[-2] = [2] * BOARD_WIDTH
        self.assertEqual(board.clear_full_lines(), 2)
        self.assertEqual(board.grid[0], [0] * BOARD_WIDTH)
        self.assertEqual(len(board.grid), BOARD_HEIGHT)

    def test_garbage_has_requested_holes(self):
        board = Board()
        self.assertFalse(board.add_garbage([2, 7]))
        self.assertEqual(board.grid[-2][2], 0)
        self.assertEqual(board.grid[-1][7], 0)
        self.assertEqual(board.grid[-1].count(GARBAGE), BOARD_WIDTH - 1)

    def test_garbage_detects_overflow(self):
        board = Board()
        board.grid[0][0] = 1
        self.assertTrue(board.add_garbage([4]))

    def test_piece_collision(self):
        board = Board()
        piece = Piece("O", x=3, y=17)
        self.assertTrue(board.can_place(piece))
        self.assertFalse(board.can_place(piece, y=19))

    def test_snapshot_round_trip(self):
        board = Board()
        board.grid[19][4] = 8
        payload = board.encode()
        self.assertEqual(Board.decode(payload), board.grid)


if __name__ == "__main__":
    unittest.main()

