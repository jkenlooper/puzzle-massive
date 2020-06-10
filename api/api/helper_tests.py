from __future__ import absolute_import
import unittest
import tempfile
import logging
import time
from uuid import uuid4
import os
import shutil
from random import randint
import json
import re

import responses

from api.app import make_app, db, redis_connection
from api.database import init_db, read_query_file, rowify
from api.constants import (
    ACTIVE,
    PUBLIC,
    CLASSIC,
)
import api.puzzle_details


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile()
        self.tmp_puzzle_resources = tempfile.mkdtemp()
        self.tmp_puzzle_archive = tempfile.mkdtemp()
        cookie_secret = "oatmeal"
        self.app = make_app(
            SQLITE_DATABASE_URI=self.tmp_db.name,
            HOSTREDIS="127.0.0.1",
            PORTREDIS=6379,
            REDIS_DB=1,
            REDIS_URL="redis://127.0.0.1:6379/1/",
            HOSTAPI="127.0.0.1",
            PORTAPI=6310,
            DEBUG=True,
            TESTING=True,  # Ignore wal journal_mode requirement
            PUZZLE_RESOURCES=self.tmp_puzzle_resources,
            PUZZLE_ARCHIVE=self.tmp_puzzle_archive,
            MINIMUM_PIECE_COUNT=20,
            MAX_POINT_COST_FOR_REBUILDING=1000,
            MAX_POINT_COST_FOR_DELETING=1000,
            BID_COST_PER_PUZZLE=100,
            POINT_COST_FOR_CHANGING_BIT=100,
            POINT_COST_FOR_CHANGING_NAME=100,
            NEW_USER_STARTING_POINTS=1300,
            POINTS_CAP=15000,
            SECURE_COOKIE_SECRET=cookie_secret,
            cookie_secret=cookie_secret,
            database_writable=True,
        )

        self.db = db
        self.app.logger.setLevel(logging.DEBUG)
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

    def tearDown(self):
        """Get rid of the temporary sqlite database and redis test db (1) after each test."""
        self.tmp_db.close()
        for tmp_dir in (self.tmp_puzzle_resources, self.tmp_puzzle_archive):
            if tmp_dir.startswith("/tmp/"):
                shutil.rmtree(tmp_dir)
            else:
                raise Exception(
                    "temp directory is not temporary? {}".format(self.tmp_dir)
                )

        with self.app.app_context():
            redis_connection.flushdb()


class PuzzleTestCase(APITestCase):
    def setUp(self):
        super().setUp()

        internal_puzzle_details_re = re.compile(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/(?P<puzzle_id>[^/]+)/details/".format(
                HOSTAPI=self.app.config["HOSTAPI"], PORTAPI=self.app.config["PORTAPI"],
            )
        )

        def request_internal_puzzle_details_callback(request):
            m = internal_puzzle_details_re.match(request.url)
            puzzle_id = m.group("puzzle_id")
            payload = json.loads(request.body)
            response_msg = api.puzzle_details.update_puzzle_details(puzzle_id, payload)
            headers = {}
            return (response_msg["status_code"], headers, json.dumps(response_msg))

        with self.app.app_context():
            responses.add_callback(
                responses.PATCH,
                internal_puzzle_details_re,
                callback=request_internal_puzzle_details_callback,
                content_type="application/json",
            )

    def tearDown(self):
        super().tearDown()
        # TODO: add anything specific for testing puzzles

    def fabricate_fake_puzzle(self, **kw):
        cur = self.db.cursor()

        classic_variant = cur.execute(
            read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}
        ).fetchone()[0]

        puzzle_id = "fabricated-{}".format(str(uuid4()))
        fake_puzzle = {
            "puzzle_id": puzzle_id,
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
        fake_puzzle.update(kw)
        puzzle_id = fake_puzzle.get("puzzle_id")

        # Create puzzle dir
        puzzle_dir = os.path.join(self.app.config.get("PUZZLE_RESOURCES"), puzzle_id)
        os.mkdir(puzzle_dir)

        # Create a blank file for the original and preview_full
        blank_original_image = os.path.join(puzzle_dir, "original.jpg")
        open(blank_original_image, "a").close()
        blank_preview_full_image = os.path.join(puzzle_dir, "preview_full.jpg")
        open(blank_preview_full_image, "a").close()

        # Add puzzle to database
        cur.execute(read_query_file("insert_puzzle.sql"), fake_puzzle)
        self.db.commit()

        # Get the puzzle id
        result = rowify(
            cur.execute(
                read_query_file("select_puzzle_id_by_puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall(),
            cur.description,
        )[0][0]
        puzzle = result["puzzle"]

        cur.execute(
            read_query_file("insert-puzzle-instance.sql"),
            {"original": puzzle, "instance": puzzle, "variant": classic_variant},
        )

        fake_puzzle = rowify(
            cur.execute(
                read_query_file("select-internal-puzzle-details-for-puzzle_id.sql"),
                {"puzzle_id": puzzle_id},
            ).fetchall(),
            cur.description,
        )[0][0]

        # Add puzzle files to database
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "original",
                "url": "/resources/{0}/original.jpg".format(
                    puzzle_id
                ),  # Not a public file (only on admin page)
            },
        )
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "preview_full",
                "url": "/resources/{0}/preview_full.jpg".format(puzzle_id),
            },
        )

        # Add puzzle instance
        classic_variant = cur.execute(
            read_query_file("select-puzzle-variant-id-for-slug.sql"), {"slug": CLASSIC}
        ).fetchone()[0]
        cur.execute(
            read_query_file("insert-puzzle-instance.sql"),
            {"original": puzzle, "instance": puzzle, "variant": classic_variant},
        )

        # Add fake piece resources
        scale = 100
        scaled_dir = os.path.join(puzzle_dir, "scale-%i" % scale)
        os.mkdir(scaled_dir)
        open(os.path.join(scaled_dir, "raster.css"), "a").close()
        open(os.path.join(scaled_dir, "raster.png"), "a").close()

        self.db.commit()

        piece_properties = []
        for pc in range(0, fake_puzzle["pieces"]):
            piece_properties.append(
                {
                    "id": pc + 1,
                    "puzzle": puzzle,
                    "x": randint(0, fake_puzzle["table_width"]),
                    "y": randint(0, fake_puzzle["table_height"]),
                    "w": 40,
                    "h": 40,
                    "r": 0,
                    "adjacent": "",
                    "rotate": 0,
                    "row": -1,
                    "col": -1,
                    "parent": None,
                    "b": 2,
                    "status": None,
                }
            )
        # Fake top left piece
        piece_properties[0]["status"] = 1
        piece_properties[0]["parent"] = 0
        piece_properties[0]["row"] = 0
        piece_properties[0]["col"] = 0

        def each(pieces):
            for p in pieces:
                yield p

        cur.executemany(read_query_file("insert_pieces.sql"), each(piece_properties))

        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "pieces",
                "url": "/resources/{puzzle_id}/scale-100/raster.png".format(
                    puzzle_id=puzzle_id
                ),
            },
        )
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "pzz",
                "url": "/resources/{puzzle_id}/scale-100/raster.css?ts={timestamp}".format(
                    puzzle_id=puzzle_id, timestamp=int(time.time())
                ),
            },
        )
        self.db.commit()
        cur.close()
        return fake_puzzle, piece_properties
