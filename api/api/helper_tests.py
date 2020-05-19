from __future__ import absolute_import
import unittest
import tempfile
import logging

from api.app import make_app, db
from api.constants import ACTIVE, PUBLIC


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile()
        self.tmp_puzzle_resources = tempfile.mkdtemp()
        self.tmp_puzzle_archive = tempfile.mkdtemp()
        cookie_secret = "oatmeal"
        self.app = make_app(
            SQLITE_DATABASE_URI=self.tmp_db.name,
            DEBUG=True,
            PUZZLE_RESOURCES=self.tmp_puzzle_resources,
            PUZZLE_ARCHIVE=self.tmp_puzzle_archive,
            SECURE_COOKIE_SECRET=cookie_secret,
            cookie_secret=cookie_secret,
        )

        self.db = db
        self.app.logger.setLevel(logging.DEBUG)

    def tearDown(self):
        """Get rid of the database after each test."""
        self.tmp_db.close()
        for tmp_dir in (self.tmp_puzzle_resources, self.tmp_puzzle_archive):
            if tmp_dir.startswith("/tmp/"):
                shutil.rmtree(tmp_dir)
            else:
                raise Exception(
                    "temp directory is not temporary? {}".format(self.tmp_dir)
                )

    def insert_puzzle_and_pieces(self, puzzle, pieces):
        def each(pieces):
            for p in pieces:
                yield p

        cur = self.db.cursor()
        cur.execute(fetch_query_string("insert_puzzle.sql"), puzzle)
        cur.executemany(fetch_query_string("insert_pieces.sql"), each(pieces))
        self.db.commit()


class PuzzleTestCase(APITestCase):
    def setUp(self):
        super().setUp()
        # TODO: add anything specific for testing puzzles

    def tearDown(self):
        super().tearDown()
        # TODO: add anything specific for testing puzzles


def make_puzzle(**kw):
    puzzle = {
        "id": 1,
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
    puzzle.update(kw)
    pieces = []
    for p in range(0, puzzle["pieces"]):
        pieces.append(
            {
                "id": p + 1,
                "puzzle": 1,
                "x": randint(0, puzzle["table_width"]),
                "y": randint(0, puzzle["table_height"]),
                "r": 0,
                "rotate": 0,
                "status": 0,
                "row": 1,
                "col": 1,
                "bg": "dark",
            }
        )
    return (puzzle, pieces)
