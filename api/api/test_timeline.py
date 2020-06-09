import unittest

from api.helper_tests import PuzzleTestCase
from api.database import fetch_query_string, rowify


class TestInternalPuzzleTimelineView(PuzzleTestCase):
    ""

    def setUp(self):
        super().setUp()
        with self.app.app_context():
            cur = self.db.cursor()
            (self.puzzle_data, self.piece_properties) = self.fabricate_fake_puzzle()
            self.puzzle = self.puzzle_data.get("id")
            self.puzzle_id = self.puzzle_data.get("puzzle_id")

    def tearDown(self):
        super().tearDown()

    def test_puzzle_exists(self):
        "Should respond with 400 HTTP error if puzzle does not exist"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(puzzle_id="abc",),
                    json={"player": 2},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(puzzle_id="abc",),
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

    def test_empty_payload_for_post(self):
        "Should respond with 400 HTTP error no payload"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

    def test_acceptable_fields_in_payload_for_post(self):
        "Should respond with 400 HTTP error if extra fields in payload were sent with POST"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                    json={"bogus": "value", "player": 2},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

    def test_acceptable_fields_in_payload_for_delete(self):
        "Should respond with 400 HTTP error if fields in payload were sent with DELETE"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                    json={"player": 2},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {
                        "msg": "No JSON payload should be sent with DELETE",
                        "status_code": 400,
                    },
                    rv.json,
                )

    def test_add_timeline_when_player_does_not_exit(self):
        "Add timeline entry with POST when player doesn't exist"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                    json={"player": 404},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {
                        "msg": "Database integrity error. Does the player ({}) exist?".format(
                            404
                        ),
                        "status_code": 400,
                    },
                    rv.json,
                )

    def test_add_timeline(self):
        "Add timeline entry with POST"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                    json={"player": 2},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 1, "msg": "Inserted", "status_code": 200,}, rv.json,
                )

    def test_delete_timeline(self):
        "Delete timeline for puzzle with DELETE"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                    json={"player": 2},
                )
                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/timeline/".format(
                        puzzle_id=self.puzzle_id,
                    ),
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 1, "msg": "Deleted", "status_code": 200,}, rv.json,
                )


if __name__ == "__main__":
    unittest.main()
