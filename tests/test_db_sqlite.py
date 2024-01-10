import sys
import os
import logging
import contextlib
import unittest
from unittest.mock import MagicMock


sys.path.append("./lib")


logger = logging.getLogger(__name__)

from db import DatabaseManager,DbBackend,DbObject,BackendErrorNotFound
from db.sqlite import SqLiteBackend
        

class TestSqLiteBackend(unittest.TestCase):
    
    DB_FILENAME = "sqlite_unit_test.db"

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)
        with contextlib.suppress(FileNotFoundError):
            os.remove(TestSqLiteBackend.DB_FILENAME)

    def setUp(self):        
        logger.debug("Setup test")
        self._backend = SqLiteBackend(TestSqLiteBackend.DB_FILENAME)
        DatabaseManager.register_backend(self._backend)
        self._backend.connection.execute("CREATE TABLE test_table (username TEXT, password TEXT)")

    def tearDown(self):
        self._backend.connection.close() 
        with contextlib.suppress(FileNotFoundError):
            os.remove(TestSqLiteBackend.DB_FILENAME)

    def create_test_user(self,username):
        # Mock DbObject
        user = MagicMock(_db_table="test_table")
        user.get_db_key.return_value = ['username',None]
        user.get_dirty_fields.return_value = {'username':username,'password':'12345678'}
        DatabaseManager.get_backend().save(user)
        return user

    def test_sqlite_create_select(self):
        """ Test sqlite create/select """
        self.create_test_user('test')
        user_data = DatabaseManager.get_backend().load_by_id('test_table',{'username':'test'})
        self.assertEqual(user_data['username'],'test')
        self.assertEqual(user_data['password'],'12345678')

    def test_sqlite_update(self):
        """ Test sqlite update """
        user  =  self.create_test_user('test')
        user.get_db_key.return_value = ['username','test']
        user.get_dirty_fields.return_value = {'password':'1234'}
        DatabaseManager.get_backend().save(user)
        user_data = DatabaseManager.get_backend().load_by_id('test_table',{'username':'test'})
        self.assertEqual(user_data['username'],'test')
        self.assertEqual(user_data['password'],'1234')


    def test_sqlite_select_list(self):
        """ Test sqlite select list """
        self.create_test_user('test1')
        # Load users list
        user_data = DatabaseManager.get_backend().load_list('test_table')
        self.assertEqual(user_data[0]['username'],'test1')
        self.assertEqual(user_data[0]['password'],'12345678')
        # Load list with filter . Empty list returned because of filter not match 
        user_data = DatabaseManager.get_backend().load_list('test_table',{'password':'12345678','username':'not_found'})
        self.assertEqual(len(user_data),0)


    def test_sqlite_delete(self):
        """ Test sqlite delete """
        user=self.create_test_user('test')
        user.get_db_key.return_value = ['username','test']
        DatabaseManager.get_backend().delete(user)
        with self.assertRaises(BackendErrorNotFound) as context:
            DatabaseManager.get_backend().load_by_id('test_table',{'username':'test'})
        self.assertEqual(str(context.exception),'Not found')


    def test_sqlite_rotate(self):
        """ Test sqlite delete """
        self._backend.connection.execute("CREATE TABLE test_audit (datetime NUMBER, user TEXT, message TEXT)")
        self._backend.connection.execute("CREATE TABLE test_audit_archive (datetime NUMBER, user TEXT, message TEXT)")
        # Latest 10 seconds ago
        latest_entry = 1 
        for entry_time in range(latest_entry,latest_entry+10,1):
            self._backend.connection.execute("INSERT INTO test_audit VALUES(?,'user',?)",(entry_time,f"message {entry_time}"))
        self.assertTrue(DatabaseManager.get_backend().rotate('test_audit',5))
        cur = self._backend.connection.cursor()
        cur.execute("SELECT * from test_audit ORDER BY datetime DESC")
        # Latest 5 should be left in main table
        left_msg_ids = [p[0] for p in cur]
        self.assertEqual(left_msg_ids,[10,9,8,7,6])
        # Others should be copied in archive
        cur.execute("SELECT * from test_audit_archive ORDER BY datetime DESC")
        other_msg_ids = [p[0] for p in cur]
        self.assertEqual(other_msg_ids,[5,4,3,2,1])
