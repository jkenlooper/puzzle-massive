from __future__ import absolute_import
import unittest

from .helper_tests import APITestCase

# Tests can be run with: `python -m unittest discover`
# Or individually `python test_example.py`

class ExampleTest(APITestCase):
    def test_get_request(self):
        "Show response"
        with self.app.test_client() as c:
            rv = c.get('/example/', follow_redirects=True)
            assert 'example get' == rv.data

if __name__ == '__main__':
    unittest.main()
