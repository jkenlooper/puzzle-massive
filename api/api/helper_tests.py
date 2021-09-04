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
import api.puzzle_file


class APITestCase(unittest.TestCase):
    debug = False

    def setUp(self):
        PUZZLE_PIECE_GROUPS = list(map(int, "100 200 400 800 1600 2200 4000 60000".split()))
        self.tmp_db = tempfile.NamedTemporaryFile()
        self.tmp_purge_list = tempfile.NamedTemporaryFile()
        self.tmp_puzzle_resources = tempfile.mkdtemp()
        self.tmp_puzzle_archive = tempfile.mkdtemp()
        cookie_secret = "oatmeal"
        self.app = make_app(
            HOST="127.0.0.1",
            HOSTNAME="legacy_puzzle_massive",
            PORT=6300,
            HOSTCACHE="127.0.0.1",
            HOSTORIGIN="127.0.0.1",
            HOSTPUBLISH="127.0.0.1",
            PORTPUBLISH=6311,
            HOSTDIVULGER="127.0.0.1",
            PORTDIVULGER=6320,
            HOSTSTREAM="127.0.0.1",
            PORTSTREAM=6321,
            CHILL_DATABASE_URI="sqlite:////var/lib/puzzle-massive/sqlite3/db",
            PUBLIC_URL_PREFIX="/site",
            ROOT_FOLDER="root",
            DOCUMENT_FOLDER="documents",
            MEDIA_FOLDER="media",
            MEDIA_PATH="/media/",
            THEME_STATIC_FOLDER="dist",
            PACKAGEJSON={"version": "0", "author": "Beaker"},
            VERSION="0",
            THEME_STATIC_PATH="/theme/0/",
            THEME_TEMPLATE_FOLDER="templates",
            THEME_SQL_FOLDER="queries",
            CACHE_NO_NULL_WARNING=True,
            CACHE_TYPE="null",
            FREEZER_DESTINATION="frozen",
            FREEZER_BASE_URL="http://legacy_puzzle_massive/",
            UNSPLASH_APPLICATION_ID="",
            UNSPLASH_APPLICATION_NAME="",
            UNSPLASH_SECRET="",
            SUGGEST_IMAGE_LINK="",
            ENVIRONMENT="development",
            NEW_PUZZLE_CONTRIB="rizzo",
            SMTP_HOST="",
            SMTP_PORT="",
            SMTP_USER="",
            SMTP_PASSWORD="",
            EMAIL_SENDER="",
            EMAIL_MODERATOR="",
            PUBLISH_WORKER_COUNT=2,
            STREAM_WORKER_COUNT=2,
            PUZZLE_PIECES_CACHE_TTL=20,
            MAX_RECENT_POINTS=25,
            RECENT_POINTS_EXPIRE=1209600,
            INITIAL_KARMA=10,
            MAX_KARMA=25,
            KARMA_POINTS_EXPIRE=3600,
            BLOCKEDPLAYER_EXPIRE_TIMEOUTS=list(
                map(int, "10 30 300 600 1200 2400 3600".split())
            ),
            MAXIMUM_PIECE_COUNT=50000,
            PUZZLE_PIECE_GROUPS=PUZZLE_PIECE_GROUPS,
            ACTIVE_PUZZLES_IN_PIECE_GROUPS=list(
                map(int, "40  20  10  10  5    5    5    5".split())
            ),
            MINIMUM_IN_QUEUE_PUZZLES_IN_PIECE_GROUPS=list(
                map(int, "6   6   2   2   1    1    1    1".split())
            ),
            SKILL_LEVEL_RANGES=list(
                zip([0] + PUZZLE_PIECE_GROUPS, PUZZLE_PIECE_GROUPS)
            ),
            MINIMUM_TO_CLAIM_ACCOUNT=1400,
            BIT_ICON_EXPIRATION=dict(
                map(
                    lambda x: [int(x[: x.index(":")]), x[1 + x.index(":") :].strip()],
                    """
            0:    2 days,
            1:    4 days,
            50:   14 days,
            400:  1 months,
            800:  4 months,
            1600: 8 months
            """.split(
                        ","
                    ),
                )
            ),
            PIECE_MOVE_TIMEOUT=4,
            MAX_PAUSE_PIECES_TIMEOUT=15,
            TOKEN_LOCK_TIMEOUT=5,
            TOKEN_EXPIRE_TIMEOUT=60 * 5,
            PLAYER_BIT_RECENT_ACTIVITY_TIMEOUT=10,
            PIECE_JOIN_TOLERANCE=100,
            AUTO_APPROVE_PUZZLES=True,
            LOCAL_PUZZLE_RESOURCES=True,
            CDN_BASE_URL="http://localhost:63812",
            PUZZLE_RESOURCES_BUCKET_REGION="local",
            PUZZLE_RESOURCES_BUCKET_ENDPOINT_URL="http://s3fake.puzzle.massive.test:4568",
            PUZZLE_RESOURCES_BUCKET="chum",
            PUZZLE_RESOURCES_BUCKET_OBJECT_CACHE_CONTROL="public, max-age:31536000, immutable",
            PUZZLE_RULES={"all"},
            PUZZLE_FEATURES={"all"},
            SHOW_OTHER_PLAYER_BITS=True,
            DOMAIN_NAME="puzzle.massive.test",
            SITE_TITLE="Test Puzzle Massive",
            HOME_PAGE_ROUTE="/chill/site/front/",
            SOURCE_CODE_LINK="https://github.com/jkenlooper/puzzle-massive/",
            M3="",
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
            PURGEURLLIST=self.tmp_purge_list.name,
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
        # TODO: set logger level to DEBUG when actively developing the tests
        # self.app.logger.setLevel(logging.WARN)
        self.app.logger.setLevel(logging.DEBUG if self.debug else logging.CRITICAL)
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
                HOSTAPI=self.app.config["HOSTAPI"],
                PORTAPI=self.app.config["PORTAPI"],
            )
        )

        def request_internal_puzzle_details_callback(request):
            m = internal_puzzle_details_re.match(request.url)
            puzzle_id = m.group("puzzle_id")
            payload = json.loads(request.body)
            response_msg = api.puzzle_details.update_puzzle_details(puzzle_id, payload)
            headers = {}
            return (response_msg["status_code"], headers, json.dumps(response_msg))

        internal_puzzle_pieces_re = re.compile(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/(?P<puzzle_id>[^/]+)/pieces/".format(
                HOSTAPI=self.app.config["HOSTAPI"],
                PORTAPI=self.app.config["PORTAPI"],
            )
        )

        def request_internal_puzzle_pieces_callback(request):
            m = internal_puzzle_pieces_re.match(request.url)
            puzzle_id = m.group("puzzle_id")
            payload = json.loads(request.body)
            response_msg = api.pieces.add_puzzle_pieces(puzzle_id, **payload)
            headers = {}
            return (response_msg["status_code"], headers, json.dumps(response_msg))

        def request_internal_puzzle_pieces_update_callback(request):
            m = internal_puzzle_pieces_re.match(request.url)
            puzzle_id = m.group("puzzle_id")
            payload = json.loads(request.body)
            response_msg = api.pieces.update_puzzle_pieces(puzzle_id, **payload)
            headers = {}
            return (response_msg["status_code"], headers, json.dumps(response_msg))

        internal_puzzle_file_re = re.compile(
            "http://{HOSTAPI}:{PORTAPI}/internal/puzzle/(?P<puzzle_id>[^/]+)/files/(?P<file_name>[^/]+)/".format(
                HOSTAPI=self.app.config["HOSTAPI"],
                PORTAPI=self.app.config["PORTAPI"],
            )
        )

        def request_internal_puzzle_file_callback(request):
            m = internal_puzzle_file_re.match(request.url)
            puzzle_id = m.group("puzzle_id")
            file_name = m.group("file_name")
            payload = json.loads(request.body)

            response_msg = api.puzzle_file.add_puzzle_file(
                puzzle_id, file_name, **payload
            )
            headers = {}
            return (response_msg["status_code"], headers, json.dumps(response_msg))

        with self.app.app_context():
            responses.add_callback(
                responses.PATCH,
                internal_puzzle_details_re,
                callback=request_internal_puzzle_details_callback,
                content_type="application/json",
            )
            responses.add_callback(
                responses.POST,
                internal_puzzle_pieces_re,
                callback=request_internal_puzzle_pieces_callback,
                content_type="application/json",
            )
            responses.add_callback(
                responses.PATCH,
                internal_puzzle_pieces_re,
                callback=request_internal_puzzle_pieces_update_callback,
                content_type="application/json",
            )
            responses.add_callback(
                responses.POST,
                internal_puzzle_file_re,
                callback=request_internal_puzzle_file_callback,
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

        puzzle_id = "fabricated-{}".format(uuid4().hex[:10])

        # These would normally have a short uuid in the name (SLIP), but to make
        # testing easier they are all static.
        preview_full_jpg = "preview_full.jpg" # preview_full.SLIP.jpg
        original_jpg = "original.jpg" # original.SLIP.jpg
        raster_css = "raster.css" # raster.SLIP.css
        raster_png = "raster.png" # raster.SLIP.png

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
        blank_original_image = os.path.join(puzzle_dir, original_jpg)
        open(blank_original_image, "a").close()
        blank_preview_full_image = os.path.join(puzzle_dir, preview_full_jpg)
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
        base_url = "" if self.app.config["LOCAL_PUZZLE_RESOURCES"] else "http://fake-cdn"
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "original",
                "url": f"{base_url}/resources/{puzzle_id}/{original_jpg}"
            },
        )
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "preview_full",
                "url": f"{base_url}/resources/{puzzle_id}/{preview_full_jpg}",
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
        open(os.path.join(scaled_dir, raster_css), "a").close()
        open(os.path.join(scaled_dir, raster_png), "a").close()

        self.db.commit()

        piece_properties = []
        for pc in range(0, fake_puzzle["pieces"]):
            piece_properties.append(
                {
                    "id": pc,
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
                "url": f"{base_url}/resources/{puzzle_id}/scale-100/{raster_png}"
            },
        )
        cur.execute(
            read_query_file("add-puzzle-file.sql"),
            {
                "puzzle": puzzle,
                "name": "pzz",
                "url": f"{base_url}/resources/{puzzle_id}/scale-100/{raster_css}?ts={int(time.time())}"
            },
        )
        self.db.commit()
        cur.close()
        return fake_puzzle, piece_properties
