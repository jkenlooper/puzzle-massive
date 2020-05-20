import unittest
import tempfile
import logging
import shutil
import os

from api.app import make_app, db
from api.tools import loadConfig
from api.database import fetch_query_string, generate_new_puzzle_id, rowify
from api.jobs.piece_forker import fork_puzzle_pieces
from api.helper_tests import PuzzleTestCase
from api.constants import (
    PUBLIC,
    PRIVATE,
    ACTIVE,
    IN_QUEUE,
    COMPLETED,
    FROZEN,
    REBUILD,
    IN_RENDER_QUEUE,
    MAINTENANCE,
    RENDERING,
    CLASSIC,
    QUEUE_NEW,
)


class TestPieceForker(PuzzleTestCase):
    ""

    def setUp(self):
        super().setUp()
        # TODO: create players

    def tearDown(self):
        super().tearDown()

    def test_fork_puzzle_pieces(self):
        ""
        with self.app.app_context():
            cur = self.db.cursor()

            # Create fake source puzzle that will be forked
            fake_puzzle = self.fabricate_fake_puzzle()
            source_puzzle_id = fake_puzzle.get("puzzle_id")

            puzzle_id = generate_new_puzzle_id("fork-puzzle")

            d = {
                "puzzle_id": puzzle_id,
                "pieces": fake_puzzle["pieces"],
                "name": fake_puzzle["name"],
                "link": fake_puzzle["link"],
                "description": "forky",
                "bg_color": "#f041EE",
                "owner": 3,
                "queue": 1,
                "status": MAINTENANCE,
                "permission": PUBLIC,
            }
            cur.execute(
                fetch_query_string("insert_puzzle.sql"), d,
            )
            db.commit()

            result = cur.execute(
                fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall()

            (result, col_names) = rowify(result, cur.description)
            puzzle_data = result[0]
            puzzle = puzzle_data["id"]

            classic_variant = cur.execute(
                fetch_query_string("select-puzzle-variant-id-for-slug.sql"),
                {"slug": CLASSIC},
            ).fetchone()[0]
            cur.execute(
                fetch_query_string("insert-puzzle-instance.sql"),
                {
                    "original": fake_puzzle["id"],
                    "instance": puzzle,
                    "variant": classic_variant,
                },
            )

            cur.execute(
                fetch_query_string("fill-user-puzzle-slot.sql"),
                {"player": 3, "puzzle": puzzle},
            )

            self.db.commit()

            fork_puzzle_pieces(fake_puzzle, puzzle_data)

            # TODO: test stuff


if __name__ == "__main__":
    unittest.main()
