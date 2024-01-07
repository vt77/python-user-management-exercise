from .base import ModelBase, ModelField
from .validator import PasswordValidator,EnumValidator


class Audit(ModelBase):
    __slots__ = ['username','password','gender','deleted']
    _db_table = 'audit'

    def __init__(self,username,message,**kwargs):
        self.username = ModelField('username',username)
        self.message = ModelField('message',message)
        super(Audit, self).__init__(**kwargs)

    def rotate(self,max_msgs:int=100):
        """ Rotate messages. If there is more then 100 records move it to archive """
        #TODO: implement by sending raw query to DatabaseManager
        pass
