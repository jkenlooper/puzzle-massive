import unittest

from api.helper_tests import PuzzleTestCase
from api.database import fetch_query_string, rowify


class TestInternalPiecesView(PuzzleTestCase):
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
                    "/internal/puzzle/{puzzle_id}/pieces/".format(puzzle_id="abc"),
                    json={"piece_properties": self.piece_properties},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(puzzle_id="abc"),
                    json={"piece_properties": self.piece_properties},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(puzzle_id="abc")
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
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    )
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No JSON data sent", "status_code": 400}, rv.json
                )

    def test_empty_payload_for_patch(self):
        "Should respond with 400 HTTP error no payload"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    )
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
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"bogus": "value", "piece_properties": []},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"bogus": "value", "piece_properties": self.piece_properties},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                def add_bogus_piece_prop(piece):
                    piece["bogus"] = "f"
                    return piece

                extra_props = list(map(add_bogus_piece_prop, self.piece_properties))
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"piece_properties": extra_props},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "has extra piece property", "status_code": 400}, rv.json,
                )

    def test_acceptable_fields_in_payload_for_patch(self):
        "Should respond with 400 HTTP error if extra fields in payload were sent with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"bogus": "value", "piece_properties": []},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"bogus": "value", "piece_properties": self.piece_properties},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

                def add_bogus_piece_prop(piece):
                    piece["bogus"] = "f"
                    return piece

                extra_props = list(map(add_bogus_piece_prop, self.piece_properties))
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"piece_properties": extra_props},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "has extra piece property", "status_code": 400}, rv.json,
                )

    def test_add_puzzle_piece_properties(self):
        "Add puzzle piece properties with POST"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.post(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"piece_properties": self.piece_properties},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {
                        "rowcount": len(self.piece_properties),
                        "msg": "Inserted",
                        "status_code": 200,
                    },
                    rv.json,
                )

    def test_update_puzzle_piece_properties_when_no_changes(self):
        "Update puzzle piece properties with PATCH when no changes"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"piece_properties": self.piece_properties},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 0, "msg": "Updated", "status_code": 200,}, rv.json,
                )

    def test_update_puzzle_piece_properties_when_some_changes(self):
        "Update puzzle piece properties with PATCH when some changes"
        with self.app.app_context():
            with self.app.test_client() as c:
                self.piece_properties[1]["x"] = 123
                self.piece_properties[1]["y"] = 123
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    ),
                    json={"piece_properties": self.piece_properties},
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 1, "msg": "Updated", "status_code": 200,}, rv.json,
                )

    def test_delete_puzzle_pieces(self):
        "Delete puzzle piece data with DELETE request"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/pieces/".format(
                        puzzle_id=self.puzzle_id
                    )
                )
                self.assertEqual(200, rv.status_code)
                self.assertEqual(
                    {"rowcount": 16, "msg": "Deleted", "status_code": 200,}, rv.json,
                )


if __name__ == "__main__":
    unittest.main()
