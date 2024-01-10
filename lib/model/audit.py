import time
import uuid as uuid_gen

from .base import ModelBase, ModelField
from .validator import NumberValidator


class Audit(ModelBase):
    __slots__ = ['uuid','message','username','datetime']
    _db_table = 'audit'

    def __init__(self,message:str,username:str=None,datetime:int=None,uuid:str=None,**kwargs):

        self.uuid = ModelField('uuid',uuid or uuid_gen.uuid4().hex,read_only=True)   
        self.username = ModelField('username',username)
        self.message = ModelField('message',message)
        self.datetime = ModelField('datetime',datetime or int(time.time()),read_only=True,ftype=int,validator=NumberValidator(minval=1000000))
        super(Audit, self).__init__(**kwargs)

    def get_db_key(self):
        return ["uuid", None if self.is_new() else self.uuid]
