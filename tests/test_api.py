import sys
import os
import logging
import unittest
from unittest.mock import MagicMock
from wsgi import app

sys.path.append("./lib")

logger = logging.getLogger(__name__)
app.testing = True


from db import DatabaseManager

backend = MagicMock()
DatabaseManager.register_backend(backend)

class TestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def test_api_get_users(self):
        client = app.test_client()
        backend.load_list.return_value = [{'username':'test1','password':'p1234','gender':'male'},{'username':'test2','password':'p4321','gender':'female'}]
        rv = client.get("/api/v1/users/")
        print(rv.data)
        self.assertNotEqual(rv.data, None)

    def test_api_get_user(self):
        client = app.test_client()
        backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.get("/api/v1/users/test1")
        print(rv.data)
        self.assertNotEqual(rv.data, None)

