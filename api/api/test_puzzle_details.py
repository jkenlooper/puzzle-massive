import unittest
import logging

from api.helper_tests import PuzzleTestCase
from api.database import fetch_query_string, rowify

# import api.puzzle_details


class TestInternalPuzzleDetailsView(PuzzleTestCase):
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
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(puzzle_id="abc")
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

    def test_missing_payload(self):
        "Should respond with 400 HTTP error if no payload was sent with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(
                        puzzle_id=self.puzzle_id
                    )
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

    def test_acceptable_fields_in_payload(self):
        "Should respond with 400 HTTP error if extra fields in payload were sent with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"bogus": "value", "pieces": 1234},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

    def test_updates_puzzle_details_with_id(self):
        "Should respond with 400 HTTP error if puzzle_id in payload"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"status": 1, "queue": 1, "pieces": 1234, "puzzle_id": "abc"},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"status": 1, "queue": 1, "pieces": 1234, "id": 123},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

    def test_updates_puzzle_details_with_values(self):
        "Should update the puzzle details with the values that were sent"
        with self.app.app_context():
            with self.app.test_client() as c:
                new_data = {"status": 1, "queue": 1, "pieces": 1234}
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/details/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json=new_data,
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"msg": "Updated", "rowcount": 1, "status_code": 200}, rv.json
                )

                self.puzzle_data.update(new_data)

                cur = self.db.cursor()
                result = cur.execute(
                    fetch_query_string(
                        "select-internal-puzzle-details-for-puzzle_id.sql"
                    ),
                    {"puzzle_id": self.puzzle_id,},
                ).fetchall()
                (result, col_names) = rowify(result, cur.description)
                self.assertEqual(result[0], self.puzzle_data)


if __name__ == "__main__":
    unittest.main()
