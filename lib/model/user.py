from .base import ModelBase, ModelField
from .validator import PasswordValidator,EnumValidator


class User(ModelBase):
    __slots__ = ['username','password','gender','deleted']
    _db_table = 'users'

    def __init__(self,username,password,gender,deleted=0,**kwargs):
        self.username = ModelField('username',username,read_only=True,unique=True)
        self.password = ModelField('password',password,validator=PasswordValidator())
        self.gender = ModelField('gender',gender,validator=EnumValidator(['male','female','other']))
        self.deleted = ModelField('gender',gender,validator=EnumValidator([0,1]))
        super(User, self).__init__(**kwargs)

    def delete(self):
        """User actually can not be deleted. Only delete flag is set
        """
        self.update('deleted',1)
        self.save()
