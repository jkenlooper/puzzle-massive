import unittest
import logging

from api.app import make_app, db
from api.tools import loadConfig
from api.database import fetch_query_string, rowify
from api.helper_tests import PuzzleTestCase
from api.constants import (
    PUBLIC,
    PRIVATE,
    ACTIVE,
    BUGGY_UNLISTED,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    REBUILD,
    IN_RENDER_QUEUE,
    MAINTENANCE,
    DELETED_REQUEST,
    RENDERING,
    CLASSIC,
    QUEUE_NEW,
)
import api.jobs.piece_reset as pr


class TestPieceReset(PuzzleTestCase):
    ""

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            cur = self.db.cursor()
            # Create fake puzzle that will be reset
            self.puzzle_data = self.fabricate_fake_puzzle()
            self.puzzle = self.puzzle_data.get("id")
            self.puzzle_id = self.puzzle_data.get("puzzle_id")

    def tearDown(self):
        super().tearDown()

    def test_verify_puzzle_exists(self):
        "Should raise error if puzzle does not exist"
        with self.app.app_context():
            with self.app.test_client() as c:
                with self.assertRaises(pr.DataError):
                    pr.reset_puzzle_pieces(1234)

    def test_status_is_updated_after_reset(self):
        "Sets status to MAINTENANCE after piece reset"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()
                pr.reset_puzzle_pieces(self.puzzle)
                result = cur.execute(
                    "select status from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.assertEqual(MAINTENANCE, result)
                cur.close()

    def test_pieces_are_updated_after_reset(self):
        "The puzzle piece positions should be randomly placed after reset"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()
                result = cur.execute(
                    "select * from Piece where puzzle = :puzzle order by id",
                    {"puzzle": self.puzzle},
                ).fetchall()
                (before_positions, cols) = rowify(result, cur.description)
                pr.reset_puzzle_pieces(self.puzzle)
                result = cur.execute(
                    "select * from Piece where puzzle = :puzzle order by id",
                    {"puzzle": self.puzzle},
                ).fetchall()
                (after_positions, cols) = rowify(result, cur.description)

                has_changed = False
                for (index, before_piece) in enumerate(before_positions):
                    after_piece = after_positions[index]
                    if (
                        before_piece["x"] != after_piece["x"]
                        or before_piece["y"] != after_piece["y"]
                    ):
                        has_changed = True
                        break

                self.assertTrue(has_changed, msg="piece positions change")
                cur.close()


if __name__ == "__main__":
    unittest.main()
