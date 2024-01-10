import sys
import logging
sys.path.append("./lib")

import unittest
logger = logging.getLogger(__name__)

from model.base import ModelBase, ModelField, ModelException
from model.validator import PasswordValidator,ValidateException
from db import DatabaseManager,DbBackend,DbObject


class MockModel(ModelBase):

    __slots__ = ['username','password']
    _db_table = 'test_table'

    def __init__(self,username:str,password:str,**kwargs):
        self.username = ModelField('username',username,read_only=True,unique=True)
        self.password = ModelField('password',password,validator=PasswordValidator())
        super(MockModel, self).__init__(**kwargs)

    def get_db_key(self):
        return ["username", None if self.is_new() else self.username]
        
class MockBackend(DbBackend):
    last_data_to_save = {}
    def save(self,model:DbBackend):
        self.last_data_to_save = model.get_dirty_fields()
    def load_by_id(self,table:str, id:dict):
        return None
    def clear(self):
        self.last_data_to_save = {}

mock_backend = MockBackend()
DatabaseManager.register_backend(mock_backend)

class TestModel(unittest.TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def test_model_create_new(self):
        """ Test new model create """

        # It should save all fields include read-only
        new_model = MockModel.create(username="test",password="12345678")
        self.assertTrue(new_model.is_new())
        new_model.save()
        self.assertEqual(mock_backend.last_data_to_save['username'],'test')
        self.assertEqual(mock_backend.last_data_to_save['password'],'12345678')
        

    def test_model_update(self):
        """ Test model update """
    
        #Emuate load model from db
        model_data = {
            'username':"test",
            'password':"pass"
        }

        new_model = MockModel(**model_data)
        self.assertFalse(new_model.is_new())
        new_model.update('password','12345')
        model_data = dict(new_model)
        self.assertEqual(model_data['username'],'test')
        self.assertEqual(model_data['password'],'12345')


    def test_model_update_save(self):
        """ Test model update save"""
    
        #Emuate load model from db
        model_data = {
            'username':"test",
            'password':"pass"
        }

        new_model = MockModel(**model_data)
        self.assertFalse(new_model.is_new())
        new_model.update('password','12345678')
        new_model.save()
        self.assertEqual(mock_backend.last_data_to_save['password'],'12345678')


    def test_model_update_save_fail_nothing_to_save(self):
        """ Test model update save fail"""
    
        #Emuate load model from db
        model_data = {
            'username':"test",
            'password':"123456"
        }

        new_model = MockModel(**model_data)
        with self.assertRaises(ModelException) as context:
            new_model.save()
        self.assertEqual(str(context.exception),'Nothing to save')

    def test_model_update_save_fail_readonly(self):
        """ Test model update save fail"""
    
        #Emuate load model from db
        model_data = {
            'username':"test",
            'password':"123456"
        }

        new_model = MockModel(**model_data)
        with self.assertRaises(ModelException) as context:
            new_model.update('username','nothing')
        self.assertEqual(str(context.exception),'Field username is read only')


    def test_model_update_save_fail_password(self):
        """ Test model update save fail"""
    
        #Emuate load model from db
        model_data = {
            'username':"test",
            'password':"123456"
        }

        new_model = MockModel(**model_data)
        new_model.update('password','s') # Password too short
        with self.assertRaises(ValidateException) as context:
            new_model.save()
        self.assertEqual(str(context.exception),'should be betwwen 6 and 12 characters length')

