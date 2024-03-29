from .base import ModelBase, ModelField
from .validator import PasswordValidator,EnumValidator
from .audit import Audit

class User(ModelBase):
    __slots__ = ['username','password','gender','deleted']
    _db_table = 'users'

    def __init__(self,username,password,gender,deleted=0,**kwargs):
        self.username = ModelField('username',username,read_only=True,unique=True)
        self.password = ModelField('password',password,validator=PasswordValidator())
        self.gender = ModelField('gender',gender,validator=EnumValidator(['male','female']))
        self.deleted = ModelField('deleted',deleted,validator=EnumValidator([0,1]),hidden=True,ftype=int)
        super(User, self).__init__(**kwargs)

    def get_db_key(self):
        return ["username", None if self.is_new() else self.username]

    def delete(self):
        """User actually can not be deleted. Only delete flag is set
        """
        self.update('deleted',1)
        self.save()
        audit = Audit.create(**{'message':f"user {self.username} deleted",'username':str(self.username)})
        audit.save()
