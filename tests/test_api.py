import sys
import os
import logging
import unittest
import json
import time
from unittest.mock import MagicMock,patch
from wsgi import app

sys.path.append("./lib")

logger = logging.getLogger(__name__)
app.testing = True

from db import DatabaseManager,BackendErrorNotFound
from model.user import User
from model.audit import Audit


class TestApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def setUp(self):
        self._backend = MagicMock()
        DatabaseManager.register_backend(self._backend)

    def test_api_get_users(self):
        client = app.test_client()
        self._backend.load_list.return_value = [{'username':'test1','password':'p1234','gender':'male','deleted':0},{'username':'test2','password':'p4321','gender':'female','deleted':0}]
        rv = client.get("/api/v1/users/")
        self.assertNotEqual(rv.data, None)
        self._backend.load_list.assert_called_once_with('users', {'deleted': 0})
        self.assertEqual(rv.json['status'],'ok')
        self.assertEqual(rv.json['payload']['items'][0],{'username':'test1','password':'p1234','gender':'male'})
        self.assertEqual(rv.json['payload']['items'][1],{'username':'test2','password':'p4321','gender':'female'})

    def test_api_get_user(self):
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.get("/api/v1/users/test1")
        self.assertNotEqual(rv.data, None)
        self._backend.load_by_id.assert_called_once_with('users', {'deleted': 0, 'username': 'test1'})
        self.assertEqual(rv.json['status'],'ok')
        self.assertEqual(rv.json['payload']['item'],{'username':'test1','password':'p1234','gender':'male'})


    def test_api_get_user_not_found(self):
        client = app.test_client()
        self._backend.load_by_id.side_effect = BackendErrorNotFound('Not found')
        rv = client.get("/api/v1/users/test1")
        self.assertNotEqual(rv.data, None)

    def test_api_create_user(self):
        client = app.test_client()
        self._backend.load_by_id.side_effect = BackendErrorNotFound('Not found')
        rv = client.post("/api/v1/users/",data=json.dumps(
            {'username':'test1','password':'p1234','gender':'male'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        user = (self._backend.save.call_args[0][0])
        self.assertEqual(user.username.value,'test1')
        self.assertEqual(user.password.value,'p1234')
        self.assertEqual(user.gender.value,'male')
        self.assertEqual(user.deleted.value,0)
        self.assertEqual(rv.json['status'],'ok')


    def test_api_create_user_exists(self):
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}

        rv = client.post("/api/v1/users/",data=json.dumps(
            {'username':'test1','password':'p1234','gender':'male'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        self.assertEqual(rv.json['status'],'error')
        self.assertEqual(rv.json['error_type'],'validation')
        self.assertEqual(rv.json['message'],'username already exists')


    def test_api_create_user_validate_error(self):
        client = app.test_client()
        self._backend.load_by_id.side_effect = BackendErrorNotFound('Not found')
        rv = client.post("/api/v1/users/",data=json.dumps(
            {'username':'test1','password':'p','gender':'male'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        print(rv.data)
        self.assertEqual(rv.json['status'],'error')
        self.assertEqual(rv.json['error_type'],'validation')
        self.assertEqual(rv.json['message'],'password should be betwwen 6 and 12 characters length')


    def test_api_create_user_validate_error_enum(self):
        client = app.test_client()
        self._backend.load_by_id.side_effect = BackendErrorNotFound('Not found')
        rv = client.post("/api/v1/users/",data=json.dumps(
            {'username':'test1','password':'p12345','gender':'wrong_enum'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        self.assertEqual(rv.json['status'],'error')
        self.assertEqual(rv.json['error_type'],'validation')
        self.assertEqual(rv.json['message'],"gender should be an one of ['male', 'female']")


    def test_api_update_user(self):
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.put("/api/v1/users/test1",data=json.dumps(
            {'password':'p12345678'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        self.assertEqual(rv.json['status'],'ok')
        user = (self._backend.save.call_args[0][0])
        updates = user.get_db_updates()
        self.assertEqual(updates['password'],'p12345678')

    def test_api_update_validation_error(self):
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.put("/api/v1/users/test1",data=json.dumps(
            {'gender':'wrong_enum'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        print(rv.data)

    def test_api_update_user_error_readonly(self):
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.put("/api/v1/users/test1",data=json.dumps(
            {'username':'test1','password':'p12345'}
            ),content_type='application/json')
        self.assertNotEqual(rv.data, None)
        self.assertEqual(rv.json['status'],'error')
        self.assertEqual(rv.json['error_type'],'model')
        self.assertEqual(rv.json['message'],"username is read only")


    @patch('model.audit.time')
    def test_api_delete_user(self,timefunc):
        """ Delete user """
        #NOTE: User actually should not be deleted, but delete flag set

        now_timestamp = int(time.time())
        timefunc.time.return_value = now_timestamp
        client = app.test_client()
        self._backend.load_by_id.return_value = {'username':'test1','password':'p1234','gender':'male'}
        rv = client.delete("/api/v1/users/test1")
        print(rv.json)
        self.assertNotEqual(rv.data, None)
        user = self._backend.save.call_args_list[0][0][0]
        self.assertIsInstance(user,User)
        updates = user.get_db_updates()
        self.assertEqual(updates,{'deleted':1})
        audit = (self._backend.save.call_args_list[1][0][0])
        self.assertIsInstance(audit,Audit)
        updates = audit.get_db_updates()
        self.assertEqual(updates['message'],'user test1 deleted')
        self.assertEqual(updates['username'],'test1')
        self.assertEqual(updates['datetime'],now_timestamp)


    def test_api_get_audits(self):
        client = app.test_client()

        audit_data = [
            {'datetime':1704893712,'username':'test1','message':'test audit for user1','uuid':'be266e0d9e1d4'},
            {'datetime':1704894712,'username':'test1','message':'test audit for user1','uuid':'46aab2bbe26'},
            ]

        self._backend.load_list.return_value = audit_data
        rv = client.get("/api/v1/audits/")
        self.assertNotEqual(rv.data, None)
        self._backend.load_list.assert_called_once_with('audit',None)
        self.assertEqual(rv.json['status'],'ok')
        self.assertDictEqual(rv.json['payload']['items'][0],audit_data[0])
        self.assertDictEqual(rv.json['payload']['items'][1],audit_data[1])


    @patch('model.audit.time')
    @patch('model.audit.uuid_gen')
    def test_api_create_audits(self,uuid_gen,timefunc):
        client = app.test_client()
        now_timestamp = int(time.time())
        timefunc.time.return_value = now_timestamp
        uuid_gen.uuid4().hex = 123456789
        audit_data = {'username':'test1','message':'test audit for user1'}
        rv = client.post("/api/v1/audits/",data=json.dumps(audit_data),content_type='application/json')
        audit = (self._backend.save.call_args[0][0])
        self.assertIsInstance(audit,Audit)
        updates = audit.get_db_updates()
        self.assertEqual(updates['message'],'test audit for user1')
        self.assertEqual(updates['username'],'test1')
        self.assertEqual(updates['datetime'],now_timestamp)
        self.assertEqual(rv.json['payload']['item']['message'],'test audit for user1')
        self.assertEqual(rv.json['payload']['item']['username'],'test1')
        self.assertEqual(rv.json['payload']['item']['datetime'],now_timestamp)


