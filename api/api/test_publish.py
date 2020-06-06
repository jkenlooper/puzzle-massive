from builtins import range
import unittest
from random import randint
from time import sleep

from api.helper_tests import APITestCase
from api.database import init_db, fetch_query_string
from api.constants import COMPLETED


def make_puzzle(**kw):
    puzzle = {
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
        "status": 1,
        "permission": 0,
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


@unittest.skip("TODO: update piece publish tests")
class PuzzlePiecesMovePublishTest(APITestCase):
    jobs = []

    def setUp(self):
        super(PuzzlePiecesMovePublishTest, self).setUp()

        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

    # def tearDown(self):
    #    for jobID in self.jobs:
    #        self.waitForJob(jobID)

    #    super(PuzzlePiecesMovePublishTest, self).tearDown()

    # def waitForJob(self, jobID):
    #    job = self.app.queue.fetch_job(jobID)
    #    while not (job.is_finished or job.is_failed):
    #        sleep(.5)

    def test_patch_request_valid(self):
        "Patch response 204 for valid requests"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # full
                data = {"x": 1, "y": 1, "r": 1}
                rv = c.patch(
                    "/puzzle/{puzzle_id}/piece/{piece}/move/".format(
                        puzzle_id=puzzle_abc.get("puzzle_id"), piece=1
                    ),
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )

                assert 204 == rv.status_code

                self.jobs.append(rv.headers.get("Job-ID"))

                # partial
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/{puzzle_id}/piece/{piece}/move/".format(
                        puzzle_id=puzzle_abc.get("puzzle_id"), piece=1
                    ),
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )

                # self.waitForJob(rv.headers.get('Job-ID'))

                assert 204 == rv.status_code

                self.jobs.append(rv.headers.get("Job-ID"))

    def test_patch_request_invalid(self):
        "Patch response 400 for invalid requests"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # empty
                data = {}
                rv = c.patch(
                    "/puzzle/abc/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

                # invalid
                data = {"frogs": 1234}
                rv = c.patch(
                    "/puzzle/abc/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

                # correct type
                data = {"x": "frog", "y": 2}
                rv = c.patch(
                    "/puzzle/abc/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

                # 400 for moving piece out of bounds
                data = {"x": -1, "y": 2}
                rv = c.patch(
                    "/puzzle/abc/piece/1/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

                # 400 for moving piece out of bounds
                data = {"x": 1, "y": 20000}
                rv = c.patch(
                    "/puzzle/abc/piece/1/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

    def test_patch_request_immutable_move(self):
        "Patch response 400 for immutable move requests"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle(status=COMPLETED)
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # 400 for moving a immutable piece. (puzzle is frozen, piece is locked)
                data = {"x": 1, "y": 2}
                rv = c.patch(
                    "/puzzle/abc/piece/12/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 400 == rv.status_code

    def test_patch_request_unauthorized(self):
        "Patch response 403 for unauthorized requests"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # 403 for moving a piece without a token
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/abc/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers={},
                )
                assert 403 == rv.status_code

                # 403 for moving a piece without a valid token
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/abc/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers={"token": "1234invalid"},
                )
                assert 403 == rv.status_code

    def test_notfound(self):
        "response 404 for notfound requests"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # not found
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/not/piece/2/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 404 == rv.status_code

                # not found
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/abc/piece/not/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 404 == rv.status_code

                # out of range
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/abc404/piece/4/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 404 == rv.status_code

                # out of range
                data = {"x": 1}
                rv = c.patch(
                    "/puzzle/abc/piece/404/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 404 == rv.status_code

    def test_notallowed(self):
        "response 405 for not allowed methods"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {"token": "1234abcd"}

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                # method not allowed
                data = {"x": 1}
                rv = c.put(
                    "/puzzle/abc/piece/1/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 405 == rv.status_code

                # method not allowed
                data = {"x": 1}
                rv = c.post(
                    "/puzzle/abc/piece/1/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 405 == rv.status_code

                # method not allowed
                data = {"x": 1}
                rv = c.get(
                    "/puzzle/abc/piece/1/move/",
                    follow_redirects=True,
                    data=data,
                    headers=headers,
                )
                assert 405 == rv.status_code

                # TODO: 429 for too many requests. Should only allow up to so many requests per token
                # https://flask-limiter.readthedocs.io/en/stable/
                #
                # TODO: 412 for precondition failed. If a piece has moved after the request was sent.


if __name__ == "__main__":
    unittest.main()
