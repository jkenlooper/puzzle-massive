import unittest
import tempfile
import logging
import shutil
import os

from api.app import make_app, db
from api.database import init_db, fetch_query_string
from api.jobs.piece_forker import fork_puzzle_pieces
from api.helper_tests import PuzzleTestCase


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
            self.app.logger.debug("hi")
            cur = self.db.cursor()

            # TODO: create fake puzzle
            source_puzzle_data = {
                "puzzle_id": "abc",
                "pieces": 16,
                "name": "abc",
                "rows": 4,
                "cols": 4,
                "piece_width": 64.0,
                "mask_width": 102.0,
                "table_width": 2000,
                "table_height": 2000,
                "name": "abc",
                "link": "http://example.com/",
                "description": "example",
                "bg_color": "gray",
                "m_date": "2016-06-24 02:59:32",
                "owner": 0,
                "queue": 2,
                "status": ACTIVE,
                "permission": PUBLIC,
            }
            cur.execute(
                fetch_query_string("insert_puzzle.sql"), source_puzzle_data,
            )

            # get puzzle that was just inserted

            cur.execute(
                fetch_query_string("add-puzzle-file.sql"),
                {
                    "puzzle": puzzle,
                    "name": "original",
                    "url": "/resources/{0}/original.jpg".format(
                        puzzle_id
                    ),  # Not a public file (only on admin page)
                },
            )

            cur.execute(
                fetch_query_string("add-puzzle-file.sql"),
                {
                    "puzzle": puzzle,
                    "name": "preview_full",
                    "url": "/resources/{0}/preview_full.jpg".format(puzzle_id),
                },
            )

            classic_variant = cur.execute(
                fetch_query_string("select-puzzle-variant-id-for-slug.sql"),
                {"slug": CLASSIC},
            ).fetchone()[0]
            cur.execute(
                fetch_query_string("insert-puzzle-instance.sql"),
                {"original": puzzle, "instance": puzzle, "variant": classic_variant},
            )

            self.db.commit()

            fork_puzzle_pieces(source_puzzle_data, puzzle_data)
            pass


if __name__ == "__main__":
    unittest.main()
