from __future__ import absolute_import
import unittest
import tempfile
import logging

from .app import make_app, db

class APITestCase(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(delete=False)
        self.app = make_app(SQLITE_DATABASE_URI=self.tmp_db.name, DEBUG=True, TESTING=True)
        self.db = db
        self.app.logger.setLevel(logging.DEBUG)


    def tearDown(self):
        """Get rid of the database after each test."""
        self.tmp_db.unlink(self.tmp_db.name)

    def insertPuzzleAndPieces(self, puzzle, pieces):
        def each(pieces):
          for p in pieces:
            yield p

        cursor = self.db.cursor()
        cursor.execute(fetch_query_string('insert_puzzle.sql'), puzzle)
        cursor.executemany(fetch_query_string('insert_pieces.sql'), each(pieces))
        self.db.commit()

