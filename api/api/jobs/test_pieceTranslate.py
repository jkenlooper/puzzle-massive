from __future__ import print_function
import os
import unittest
import tempfile
import redis
import sqlite3

from api.database import rowify
from api.jobs.convertPiecesToRedis import convert
from api.jobs.pieceTranslate import translate

redisConnection = redis.from_url("redis://localhost:6379/0/", decode_responses=True)


@unittest.skip("TODO: update piece translate tests")
class JobTestCase(unittest.TestCase):
    puzzles = []

    def setUp(self):
        self.query_puzzle_255 = "select id as puzzle, table_width, table_height, mask_width, puzzle_id, pieces from Puzzle where id = 255"
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db = sqlite3.connect(self.tmp_db.name)
        cur = self.db.cursor()

        for file_path in (
            "../queries/create_table_puzzle.sql",
            "../queries/create_table_piece.sql",
            "../queries/create_table_user.sql",
            "../queries/create_table_timeline.sql",
            "examplePuzzle.sql",
            "examplePiece.sql",
        ):
            with open(
                os.path.normpath(os.path.join(os.path.dirname(__file__), file_path)),
                "r",
            ) as f:
                for statement in f.read().split(";"):
                    # print statement
                    cur.execute(statement)
                    self.db.commit()

        (results, col_names) = rowify(
            cur.execute("select id as puzzle from Puzzle"), cur.description
        )

        for result in results:
            self.puzzles.append(result["puzzle"])
            convert(result["puzzle"], db_file=self.tmp_db.name)

        cur.close()

    def tearDown(self):
        """Get rid of the database after each test."""
        self.tmp_db.unlink(self.tmp_db.name)

        # return
        for puzzle in self.puzzles:
            print("Clean up for puzzle: {0}".format(puzzle))
            # Piece Properties
            keys = redisConnection.keys(pattern="pc:{puzzle}:*".format(puzzle=puzzle))
            if len(keys) > 0:
                deleted = redisConnection.delete(*keys)
                print("Deleted {deleted} piece properties".format(**locals()))

            # Piece Group
            keys = redisConnection.keys(pattern="pcg:{puzzle}:*".format(puzzle=puzzle))
            if len(keys) > 0:
                deleted = redisConnection.delete(*keys)
                print("Deleted {deleted} piece group".format(**locals()))

            # Piece Fixed
            deleted = redisConnection.delete("pcfixed:{puzzle}".format(puzzle=puzzle))
            print("Deleted {deleted} piece fixed".format(**locals()))

            # Piece Stacked
            deleted = redisConnection.delete("pcstacked:{puzzle}".format(puzzle=puzzle))
            print("Deleted {deleted} piece stacked".format(**locals()))

            # Piece X
            deleted = redisConnection.delete("pcx:{puzzle}".format(puzzle=puzzle))
            print("Deleted {deleted} piece x".format(**locals()))

            # Piece Y
            deleted = redisConnection.delete("pcy:{puzzle}".format(puzzle=puzzle))
            print("Deleted {deleted} piece y".format(**locals()))

    def test_simple(self):
        ""
        assert True == True

    def test_proximity(self):
        "Proximity"
        cur = self.db.cursor()
        r = 0

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]

        (piece, x, y) = (6, 113, 69)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # No other pieces in proximity
        assert ":{piece}:{x}:{y}:0::".format(**locals()) == msg

        (piece, x, y) = (5, 86, 74)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 6 is in proximity so reset the status of both
        expectedMsg = ":6:::::\n:{piece}:::::\n:{piece}:{x}:{y}:0::".format(**locals())
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

        (piece, x, y) = (0, 75, 82)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 6 and 5 are in proximity so reset the status of all three
        expectedMsg = ":6:::::\n:5:::::\n:{piece}:::::\n:{piece}:{x}:{y}:270::".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

        (piece, x, y) = (7, 119, 76)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 6, 5, and 0 are in proximity so set status to 2
        expectedMsg = ":6:::::2\n:5:::::2\n:0:::::2\n:{piece}:::::2\n:{piece}:{x}:{y}:180::2".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

        (piece, x, y) = (7, 40, 726)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 7 moved away from 6, 5, and 0; proximity status isn't changed for those
        expectedMsg = ":{piece}:{x}:{y}:180::".format(**locals())
        print("({0})".format(expectedMsg))
        print("[{0}]".format(msg))
        assert expectedMsg == msg

        cur.close()

    def test_single_piece_move(self):
        "Move a piece"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]

        piece = 0
        x = 68
        y = 68
        r = 0
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        assert "move:{puzzle_id}".format(**testPuzzle) == topic
        assert ":0:68:68:270::" == msg

    def test_move_two_pieces_in_group(self):
        "Move two pieces that are grouped"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        (piece, x, y) = (10, 634, 39)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Pieces 10 and 9 are grouped. 10 gets moved and then 9 moves as well.
        expectedMsg = ":{piece}:{x}:{y}:0:10:\n:9:634:104:::".format(**locals())
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_three_pieces_in_group(self):
        "Move three pieces that are grouped"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        (piece, x, y) = (11, 368, 31)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Pieces 11, 1 and 8 are grouped. 11 gets moved and then the others move as well.
        expectedMsg = ":{piece}:{x}:{y}:90:8:\n:1:433:31:::\n:8:303:31:::".format(
            **locals()
        )
        print("({0})".format(expectedMsg))
        print("[{0}]".format(msg))
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_one_piece_into_group_with_two_pieces(self):
        "Move non-grouped piece to a group with 2 pieces"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        (piece, x, y) = (0, 414, 661)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 0 is moved to join piece 10 which is in group 10
        expectedMsg = ":{piece}:{x}:{y}:270::\n:{piece}:430:657:270:10:\n:10::::10:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_one_piece_into_group_with_three_pieces(self):
        "Move non-grouped piece to a group with 3 pieces"
        cur = self.db.cursor()
        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        (piece, x, y) = (7, 651, 541)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 7 is moved to join piece 8 which is in group 8
        expectedMsg = ":{piece}:{x}:{y}:180::\n:{piece}:672:527:180:8:\n:8::::8:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_join_two_pieces_not_in_group(self):
        "Join two pieces that are not grouped"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        (piece, x, y) = (6, 54, 61)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        (piece, x, y) = (5, 130, 77)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 5 gets shifted to join piece 6, piece group 6 is created and both pieces join
        expectedMsg = ":{piece}:{x}:{y}:0::\n:5:119:61:0:6:\n:6::::6:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_join_two_grouped_pieces_to_a_piece_not_grouped(self):
        "Join two grouped pieces to a piece not grouped"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move piece 7
        (piece, x, y) = (7, 55, 118)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        (piece, x, y) = (3, 46, 196)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        # Piece 3 and 2 are grouped, 3 is moved to join piece 7
        expectedMsg = ":{piece}:{x}:{y}:0:3:\n:7::::3:\n:2:120:183:::\n:3:55:183:0:3:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_join_two_pieces_that_are_both_in_group(self):
        "Join two pieces that are grouped when moving piece group is smaller or same size"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move piece 9 which is in group 10
        (piece, x, y) = (9, 809, 139)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        # Move piece 2 to join piece 9; group 3 pieces are now in group 10
        (piece, x, y) = (2, 731, 140)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        expectedMsg = ":{piece}:{x}:{y}:270:3:\n:3:679:139::10:\n:2::::10:\n:2:744:139:270:10:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_join_two_pieces_that_are_both_in_group_when_adjacent_group_smaller(self):
        "Join two pieces that are grouped when moving piece group is larger then adjacent piece group"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move piece 1 to join piece 10. Piece 1 is in larger group 8, and piece 10 is in smaller group 10
        # (1,8,11) (9,10)
        (piece, x, y) = (1, 499, 580)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        expectedMsg = ":{piece}:{x}:{y}:0:8:\n:9::::8:\n:10::::8:\n:8:365:592:::\n:11:430:592:::\n:1:495:592:0:8:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_piece_to_join_immovable(self):
        "Move a piece to join immovable group"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move 6 to join piece 4 which is immovable
        (piece, x, y) = (6, 446, 222)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        expectedMsg = ":{piece}:{x}:{y}:0::\n:6:428:218:0:4:1\n:4::::4:".format(
            **locals()
        )
        print("({0})".format(expectedMsg))
        print("[{0}]".format(msg))
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_grouped_piece_to_join_immovable(self):
        "Move a grouped piece to join immovable group"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move 8 to join piece 4 which is immovable
        # (8,1,11) -> 4
        (piece, x, y) = (8, 367, 296)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        expectedMsg = ":{piece}:{x}:{y}:90:8:\n:1:493:283::4:1\n:11:428:283::4:1\n:8::::4:\n:8:363:283:90:4:1".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_second_piece_to_join_immovable(self):
        "Move a piece to join immovable group and then join another piece to that one"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move 6 to join 4 which is immovable
        (piece, x, y) = (6, 438, 218)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        expectedMsg = ":{piece}:{x}:{y}:0::\n:6:428:218:0:4:1\n:4::::4:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

        # Move 5 to join 6 which is immovable
        (piece, x, y) = (5, 523, 210)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )

        expectedMsg = ":{piece}:{x}:{y}:0::\n:5:493:218:0:4:1\n:6::::4:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

    def test_move_second_piece_group_to_join_immovable(self):
        "Move a piece to join immovable group and then join another piece group to that one"
        cur = self.db.cursor()

        (results, col_names) = rowify(
            cur.execute(self.query_puzzle_255), cur.description
        )
        testPuzzle = results[0]
        r = 0

        # Move 6 to join 4 which is immovable
        (piece, x, y) = (6, 437, 232)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        expectedMsg = ":{piece}:{x}:{y}:0::\n:6:428:218:0:4:1\n:4::::4:".format(
            **locals()
        )
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg

        # Move 11 to join immovable piece 6
        (piece, x, y) = (11, 436, 293)
        (topic, msg) = translate(
            0, testPuzzle, piece, x, y, r, db_file=self.tmp_db.name
        )
        expectedMsg = ":{piece}:{x}:{y}:90:8:\n:1:493:283::4:1\n:8:363:283::4:1\n:11::::4:\n:11:428:283:90:4:1".format(
            **locals()
        )
        print("({0})".format(expectedMsg))
        print("[{0}]".format(msg))
        assert len(expectedMsg) == len(msg)
        for l in expectedMsg.split("\n"):
            assert l in msg


if __name__ == "__main__":
    unittest.main()
