import unittest

from api.helper_tests import PuzzleTestCase
from api.database import fetch_query_string, rowify


class TestInternalPuzzleFileView(PuzzleTestCase):
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
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id="abc", file_name="pzz"
                    ),
                    json={"url": "/something/raster.css?whatever"},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id="abc", file_name="pzz"
                    ),
                    json={"url": "/something/raster.css?whatever"},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "No puzzle found", "status_code": 400}, rv.json
                )

                rv = c.delete(
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id="abc", file_name="pzz"
                    ),
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
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id=self.puzzle_id, file_name="pzz"
                    ),
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
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id=self.puzzle_id, file_name="pzz"
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
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id=self.puzzle_id, file_name="pzz"
                    ),
                    json={"bogus": "value", "url": "/something/raster.css?whatever"},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {"msg": "Extra fields in JSON data were sent", "status_code": 400},
                    rv.json,
                )

    def test_acceptable_fields_in_payload_for_patch(self):
        "Should respond with 400 HTTP error if extra fields in payload were sent with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                rv = c.patch(
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id=self.puzzle_id, file_name="pzz"
                    ),
                    json={"bogus": "value", "url": "/something/raster.css?whatever"},
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
                    "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                        puzzle_id=self.puzzle_id, file_name="pzz"
                    ),
                    json={"url": "/something/raster.css?whatever"},
                )
                self.assertEqual(400, rv.status_code)
                self.assertEqual(
                    {
                        "msg": "No JSON payload should be sent with DELETE",
                        "status_code": 400,
                    },
                    rv.json,
                )

    def test_add_puzzle_file_that_is_not_supported(self):
        "Add puzzle file url that is not supported with POST"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("resized-original", "/something/original.jpg"),
                    ("preview", "/something/preview_full.jpg"),
                    ("bigfoot", "/something/bigfoot.jpg"),
                ]:
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={"url": url},
                    )
                    self.assertEqual(400, rv.status_code)
                    self.assertEqual(
                        {
                            "msg": "File with that name is not supported",
                            "status_code": 400,
                        },
                        rv.json,
                    )

    def test_update_puzzle_file_that_is_not_supported(self):
        "Update puzzle file url that is not supported with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("resized-original", "/something/original.jpg"),
                    ("preview", "/something/preview_full.jpg"),
                    ("bigfoot", "/something/bigfoot.jpg"),
                ]:
                    rv = c.patch(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={"url": url},
                    )
                    self.assertEqual(400, rv.status_code)
                    self.assertEqual(
                        {
                            "msg": "File with that name is not supported",
                            "status_code": 400,
                        },
                        rv.json,
                    )

    def test_add_puzzle_file_that_does_not_support_attribution(self):
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("pzz", "/something/raster.css?whatever"),
                    ("pieces", "/something/raster.png"),
                ]:
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={
                            "url": url,
                            "attribution": {
                                "title": "Photo",
                                "author_link": "...",
                                "author_name": "...",
                                "source": "...",
                                "license": "unsplash",
                            },
                        },
                    )
                    self.assertEqual(400, rv.status_code)
                    self.assertEqual(
                        {
                            "msg": "File with that name does not support adding attribution",
                            "status_code": 400,
                        },
                        rv.json,
                    )

    def test_update_puzzle_file_that_does_not_support_attribution(self):
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("pzz", "/something/raster.css?whatever"),
                    ("pieces", "/something/raster.png"),
                ]:
                    rv = c.patch(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={
                            "url": url,
                            "attribution": {
                                "title": "Photo",
                                "author_link": "https://example.com/new-author",
                                "author_name": "...",
                                "source": "...",
                                "license": "unsplash",
                            },
                        },
                    )
                    self.assertEqual(400, rv.status_code)
                    self.assertEqual(
                        {
                            "msg": "File with that name does not support adding attribution",
                            "status_code": 400,
                        },
                        rv.json,
                    )

    def test_add_puzzle_file_that_does_support_attribution(self):
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("original", "/something/original.jpg"),
                    ("preview_full", "/something/preview_full.jpg"),
                ]:
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={
                            "url": url,
                            "attribution": {
                                "title": "Photo",
                                "author_link": "https://example.com/author_link",
                                "author_name": "test author",
                                "source": "https://example.com/author_link",
                                "license_name": "unsplash",
                            },
                        },
                    )
                    self.assertEqual(200, rv.status_code)
                    self.assertEqual(
                        {"rowcount": 1, "msg": "Inserted", "status_code": 200,},
                        rv.json,
                    )

    def test_update_puzzle_file_that_does_support_attribution(self):
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("original", "/something/original.jpg"),
                    ("preview_full", "/something/preview_full.jpg"),
                ]:
                    rv = c.delete(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        )
                    )
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={
                            "url": url,
                            "attribution": {
                                "title": "Photo",
                                "author_link": "...",
                                "author_name": "...",
                                "source": "...",
                                "license_name": "unsplash",
                            },
                        },
                    )
                    rv = c.patch(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={
                            "url": url,
                            "attribution": {
                                "title": "Photo",
                                "author_link": "https://example.com/author_link",
                                "author_name": "test author",
                                "source": "https://example.com/author_link",
                                "license_name": "unsplash",
                            },
                        },
                    )
                    self.assertEqual(200, rv.status_code)
                    self.assertEqual(
                        {"rowcount": 1, "msg": "Updated", "status_code": 200,}, rv.json,
                    )

    def test_add_puzzle_file(self):
        "Add puzzle file url with POST"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("pzz", "/something/raster.css?whatever"),
                    ("pieces", "/something/raster.png"),
                ]:
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={"url": url},
                    )
                    self.assertEqual(200, rv.status_code)
                    self.assertEqual(
                        {"rowcount": 1, "msg": "Inserted", "status_code": 200,},
                        rv.json,
                    )

    def test_update_puzzle_file(self):
        "Update puzzle file url with PATCH"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("pzz", "/something/raster.css?whatever"),
                    ("pieces", "/something/raster.png"),
                ]:
                    rv = c.delete(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                    )
                    rv = c.post(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={"url": url},
                    )
                    rv = c.patch(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                        json={"url": url},
                    )
                    self.assertEqual(200, rv.status_code)
                    self.assertEqual(
                        {"rowcount": 1, "msg": "Updated", "status_code": 200,}, rv.json,
                    )

    def test_delete_puzzle_file_that_is_not_supported(self):
        "Delete puzzle file url that is not supported with DELETE"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("bigfoot", "/something/bigfoot.jpg"),
                ]:
                    rv = c.delete(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                    )
                    self.assertEqual(400, rv.status_code)
                    self.assertEqual(
                        {
                            "msg": "File with that name is not supported",
                            "status_code": 400,
                        },
                        rv.json,
                    )

    def test_delete_puzzle_file(self):
        "Delete puzzle file url with DELETE"
        with self.app.app_context():
            with self.app.test_client() as c:
                for (name, url) in [
                    ("pzz", "/something/raster.css?whatever"),
                    ("pieces", "/something/raster.png"),
                ]:
                    rv = c.delete(
                        "/internal/puzzle/{puzzle_id}/files/{file_name}/".format(
                            puzzle_id=self.puzzle_id, file_name=name
                        ),
                    )
                    self.assertEqual(200, rv.status_code)
                    self.assertEqual(
                        {"rowcount": 1, "msg": "Deleted", "status_code": 200,}, rv.json,
                    )


if __name__ == "__main__":
    unittest.main()
