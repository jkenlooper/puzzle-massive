import unittest
import tempfile
import logging
import shutil
import os

import responses

from api.app import make_app, db
from api.tools import loadConfig
from api.database import fetch_query_string, generate_new_puzzle_id, rowify
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
import api.jobs.piece_forker as pf


class TestPieceForker(PuzzleTestCase):
    ""

    def setUp(self):
        super().setUp()

        with self.app.app_context():
            cur = self.db.cursor()
            # TODO: create players

            # Create fake source puzzle that will be forked
            (
                fake_source_puzzle_data,
                fake_source_piece_properties,
            ) = self.fabricate_fake_puzzle()
            self.source_puzzle_id = fake_source_puzzle_data.get("puzzle_id")

            result = cur.execute(
                fetch_query_string(
                    "select-valid-puzzle-for-new-puzzle-instance-fork.sql"
                ),
                {
                    "puzzle_id": self.source_puzzle_id,
                    "ACTIVE": ACTIVE,
                    "IN_QUEUE": IN_QUEUE,
                    "COMPLETED": COMPLETED,
                    "FROZEN": FROZEN,
                },
            ).fetchall()
            if not result:
                raise Exception("fake puzzle failed")
            (result, col_names) = rowify(result, cur.description)
            self.source_puzzle_data = result[0]

            self.puzzle_id = generate_new_puzzle_id("fork-puzzle")

            d = {
                "puzzle_id": self.puzzle_id,
                "pieces": self.source_puzzle_data["pieces"],
                "name": self.source_puzzle_data["name"],
                "link": self.source_puzzle_data["link"],
                "description": "forky",
                "bg_color": "#f041EE",
                "owner": 3,
                "queue": 1,
                "status": MAINTENANCE,
                "permission": PRIVATE,
            }
            cur.execute(
                fetch_query_string("insert_puzzle.sql"), d,
            )
            db.commit()

            result = cur.execute(
                fetch_query_string("select-all-from-puzzle-by-puzzle_id.sql"),
                {"puzzle_id": self.puzzle_id},
            ).fetchall()

            (result, col_names) = rowify(result, cur.description)
            self.puzzle_data = result[0]
            puzzle = self.puzzle_data["id"]

            classic_variant = cur.execute(
                fetch_query_string("select-puzzle-variant-id-for-slug.sql"),
                {"slug": CLASSIC},
            ).fetchone()[0]
            cur.execute(
                fetch_query_string("insert-puzzle-instance.sql"),
                {
                    "original": self.source_puzzle_data["id"],
                    "instance": puzzle,
                    "variant": classic_variant,
                },
            )

            cur.execute(
                fetch_query_string("fill-user-puzzle-slot.sql"),
                {"player": 3, "puzzle": puzzle},
            )

            self.db.commit()

    def tearDown(self):
        super().tearDown()

    @responses.activate
    def test_maintenance_status(self):
        "Should be in maintenance mode when forking the puzzle"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()
                result = cur.execute(
                    "select status from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.assertEqual(MAINTENANCE, result)

                pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)

                result = cur.execute(
                    "select status from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.app.logger.debug(result)
                self.assertEqual(ACTIVE, result)

    def test_maintenance_status_exception(self):
        "Should raise exception if not in maintenance"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()
                cur.execute(
                    "update Puzzle set status = :status where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id, "status": ACTIVE},
                )
                self.db.commit()
                with self.assertRaises(pf.DataError):
                    pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)
                cur.close()

    def test_instance_puzzle_exists_exception(self):
        "Should raise exception if instance puzzle doesn't exist"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()
                cur.execute(
                    "delete from PuzzleInstance where instance = :instance",
                    {"instance": self.puzzle_data["id"]},
                )
                self.db.commit()
                with self.assertRaises(pf.DataError):
                    pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)
                cur.close()

    @responses.activate
    def test_instance_puzzle_has_copy_of_resources(self):
        "Instance puzzle should have copy of resource files from original"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()

                pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)

                puzzle_dir = os.path.join(
                    self.app.config["PUZZLE_RESOURCES"], self.puzzle_id
                )

                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "original.jpg"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "preview_full.jpg"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "scale-100", "raster.css"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "scale-100", "raster.png"))
                )

                query_puzzle_file = (
                    "select url from PuzzleFile where name = :name and puzzle = :puzzle"
                )
                result = cur.execute(
                    query_puzzle_file,
                    {"name": "pieces", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/scale-100/raster.png".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result,
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "pzz", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/scale-100/raster.css".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result[0 : result.index("?")],
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "original", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/original.jpg".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result,
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "preview_full", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/preview_full.jpg".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result,
                )

                cur.close()

    @responses.activate
    def test_instance_puzzle_has_copy_of_unsplash_preview_full_url(self):
        "Instance puzzle should have copy of preview full url when not local from original"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()

                # Set non-local url for preview_full
                # "https://images.example.com/cat.jpg" and remove the
                # source puzzle preview_full image.
                source_puzzle_dir = os.path.join(
                    self.app.config["PUZZLE_RESOURCES"], self.source_puzzle_id
                )
                blank_preview_full_image = os.path.join(
                    source_puzzle_dir, "preview_full.jpg"
                )
                os.unlink(blank_preview_full_image)
                cur.execute(
                    "update PuzzleFile set url = :url where name = :name and puzzle = :puzzle;",
                    {
                        "name": "preview_full",
                        "puzzle": self.source_puzzle_data["id"],
                        "url": "https://images.example.com/cat.jpg",
                    },
                )
                self.db.commit()

                pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)

                puzzle_dir = os.path.join(
                    self.app.config["PUZZLE_RESOURCES"], self.puzzle_id
                )

                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "original.jpg"))
                )
                self.assertFalse(
                    os.path.exists(os.path.join(puzzle_dir, "preview_full.jpg"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "scale-100", "raster.css"))
                )
                self.assertTrue(
                    os.path.exists(os.path.join(puzzle_dir, "scale-100", "raster.png"))
                )

                query_puzzle_file = (
                    "select url from PuzzleFile where name = :name and puzzle = :puzzle"
                )
                result = cur.execute(
                    query_puzzle_file,
                    {"name": "pieces", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/scale-100/raster.png".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result,
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "pzz", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/scale-100/raster.css".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result[0 : result.index("?")],
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "original", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "/resources/{puzzle_id}/original.jpg".format(
                        puzzle_id=self.puzzle_id
                    ),
                    result,
                )

                result = cur.execute(
                    query_puzzle_file,
                    {"name": "preview_full", "puzzle": self.puzzle_data["id"]},
                ).fetchone()[0]
                self.assertEqual(
                    "https://images.example.com/cat.jpg", result,
                )

                cur.close()

    @responses.activate
    def test_change_to_complete_status(self):
        "Should switch status to completed if all the pieces have been joined"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()

                cur.execute(
                    "update Piece set parent = 2 where puzzle = :puzzle",
                    {"puzzle": self.source_puzzle_data["id"]},
                )
                cur.execute(
                    "update Puzzle set status = :COMPLETED where id = :puzzle",
                    {"puzzle": self.source_puzzle_data["id"], "COMPLETED": COMPLETED},
                )
                self.source_puzzle_data["status"] = COMPLETED

                result = cur.execute(
                    "select status from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.assertEqual(MAINTENANCE, result)

                pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)

                result = cur.execute(
                    "select status from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.assertEqual(COMPLETED, result)

    @responses.activate
    def test_permission_is_not_public(self):
        "Copied puzzles are not public"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()

                pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)

                result = cur.execute(
                    "select permission from Puzzle where puzzle_id = :puzzle_id",
                    {"puzzle_id": self.puzzle_id},
                ).fetchone()[0]
                self.assertEqual(PRIVATE, result)

    def test_status_of_puzzle(self):
        "Source puzzle needs to be in the correct status for copying"
        with self.app.app_context():
            with self.app.test_client() as c:
                cur = self.db.cursor()

                not_acceptable_statuses = [BUGGY_UNLISTED, MAINTENANCE, DELETED_REQUEST]
                for status in not_acceptable_statuses:
                    self.source_puzzle_data["status"] = status
                    with self.assertRaises(pf.DataError):
                        pf.fork_puzzle_pieces(self.source_puzzle_data, self.puzzle_data)


if __name__ == "__main__":
    unittest.main()
