import unittest

from flask import current_app

from api.helper_tests import PuzzleTestCase


class TestInternalPuzzleRenderedResourcesListView(PuzzleTestCase):
    "Should return a response"

    debug = True

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def test_fetch_list_for_local_puzzles(self):
        ""
        with self.app.app_context():

            current_app.config["LOCAL_PUZZLE_RESOURCES"] = True
            (puzzle_data, _) = self.fabricate_fake_puzzle()
            puzzle = puzzle_data.get("id")
            puzzle_id = puzzle_data.get("puzzle_id")

            with self.app.test_client() as c:
                rv = c.get(
                    "/internal/puzzle-rendered-resources-list/?url_match=/resources/%"
                )
                self.app.logger.debug(rv.json)
                self.assertEqual(200, rv.status_code)
                self.assertEqual(4, len(rv.json["puzzle_files"]))

    def test_fetch_list_for_non_local_puzzles(self):
        ""
        with self.app.app_context():

            current_app.config["LOCAL_PUZZLE_RESOURCES"] = False
            (puzzle_data, _) = self.fabricate_fake_puzzle()
            puzzle = puzzle_data.get("id")
            puzzle_id = puzzle_data.get("puzzle_id")

            with self.app.test_client() as c:
                rv = c.get(
                    "/internal/puzzle-rendered-resources-list/?url_match=http://fake-cdn/resources/%"
                )
                self.app.logger.debug(rv.json)
                self.assertEqual(200, rv.status_code)
                self.assertEqual(4, len(rv.json["puzzle_files"]))


if __name__ == "__main__":
    unittest.main()
