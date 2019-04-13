from __future__ import absolute_import
import unittest

from .app import db
from .database import init_db, rowify

from .helper_tests import APITestCase

class DatabaseTest(APITestCase):
    def test_connection(self):
        "Connection to db"
        with self.app.app_context():
            with self.app.test_client() as c:

                cursor = db.cursor()
                result = cursor.execute("select 'test' as test")
                (result, col_names) = rowify(result, cursor.description)
                assert result[0]['test'] == 'test'

    def test_init(self):
        "Initialize db"
        with self.app.app_context():
            with self.app.test_client() as c:
                init_db()

                cursor = db.cursor()
                result = cursor.execute("select * from Puzzle")
                (result, col_names) = rowify(result, cursor.description)
                assert set(col_names) == set([
                    'id',
                    'puzzle_id',
                    'pieces',
                    'rows',
                    'cols',
                    'piece_width',
                    'mask_width',
                    'table_width',
                    'table_height',
                    'name',
                    'link',
                    'description',
                    'bg_color',
                    'm_date',
                    'owner',
                    'queue',
                    'status',
                    'permission',
                    ])

                result = cursor.execute("select * from Piece")
                (result, col_names) = rowify(result, cursor.description)
                assert set(col_names) == set([
                    'id',
                    'puzzle',
                    'x',
                    'y',
                    'r',
                    'rotate',
                    'row',
                    'col',
                    'parent',
                    'top_path',
                    'right_path',
                    'bottom_path',
                    'left_path',
                    'status',
                    'bg',
                    ])

if __name__ == '__main__':
    unittest.main()
