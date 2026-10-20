import unittest

from tetris.pieces import PieceGenerator


class PieceGeneratorTest(unittest.TestCase):
    def test_same_seed_produces_same_sequence(self):
        first = PieceGenerator(123456)
        second = PieceGenerator(123456)
        self.assertEqual(
            [first.next_kind() for _ in range(50)],
            [second.next_kind() for _ in range(50)],
        )

    def test_each_bag_contains_all_seven_types(self):
        generator = PieceGenerator(10)
        bag = [generator.next_kind() for _ in range(7)]
        self.assertEqual(set(bag), set("IJLOSTZ"))


if __name__ == "__main__":
    unittest.main()

