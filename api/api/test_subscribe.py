from __future__ import print_function
import unittest

from websocket import create_connection

from api.helper_tests import APITestCase

class PuzzlePiecesMoveSubscribeTest(APITestCase):

    def offtest_subscribe(self):
        "subscribe"
        with self.app.app_context():
            with self.app.test_client() as c:
                headers = {
                        'token': '1234abcd'
                        }

                (puzzle_abc, pieces_abc) = make_puzzle()
                self.insertPuzzleAndPieces(puzzle_abc, pieces_abc)

                data = { 'x': 1, 'y': 1, 'r': 1 }
                rv = c.patch('/puzzle/{puzzle_id}/piece/{piece}/move/'.format(puzzle_id=puzzle_abc.get('puzzle_id'), piece=1), follow_redirects=True, data=data, headers=headers)

                assert 204 == rv.status_code

                self.jobs.append(rv.headers.get('Job-ID'))

    def test_socket(self):
        "wsdump.py ws://localhost:5000/echo"

        ws = create_connection("ws://echo.websocket.org/")
        print("Sending 'Hello, World'...")
        ws.send("Hello, World")
        print("Sent")
        print("Receiving...")
        result =  ws.recv()
        print("Received '%s'" % result)
        assert result == "Hello, World"
        ws.close()
