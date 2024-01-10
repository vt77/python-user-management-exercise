
import logging
from abc import ABC
import contextlib

from db import DatabaseManager, DbObject, BackendErrorNotFound
from .validator import AsciiValidator,ValidateException

class ModelException(Exception):
    """Model error handling exeption"""

logger = logging.getLogger(__name__)

class Model(ABC):
    
    def validate(self):
        """Validate model before save/create
        """
        raise NotImplementedError

    def save(self):
        """Save model using database backend
        """
        raise NotImplementedError

    @classmethod
    def create(cls,params):
        """Create new model

        Args:
            params (dict): parameters specified to model

        Returns:
            Model: newly created model
        """
        raise NotImplementedError
        

class ModelField:
    name = None
    _value = None
    validator = None
    read_only = False
    unique = False
    hidden = False
    _type = None

    def __init__(self,name:str,value:str=None,validator=None,read_only=False, unique=False, hidden=False, ftype=str):
        self.name = name
        self._value = value
        self.validator = validator
        if not self.validator:
            self.validator = AsciiValidator()
        self.read_only = read_only
        self.unique = unique
        self.hidden = hidden
        self._type = ftype

    def __str__(self):
        return str(self._value)


    @property
    def value(self):
        return self._type(self._value)

    @value.setter
    def value(self,value):
        self._value = value

    def validate(self):
        if not self.validator:
            raise ModelException("No validator defined for field %s",self.name)
        logger.debug("Validate field %s using %s",self.name,self.validator)
        self.validator.validate(self)

class ModelBase(Model,DbObject):
    
    _is_new = False
    _duty_fields = {}
    _validated_data = None

    def __init__(self,is_new=False):
        self._is_new = is_new
        self._duty_fields = set(self.__slots__) if is_new else set()

    def validate(self) -> dict:
        """

        Raises:
            ModelException: on model errors
            ValidateException: on validation error

        Returns:
            dict: dict of names-values to save in db
        """
        validated_data = {}
        for field in self._duty_fields:
            f = getattr(self,field)
            if not isinstance(f,ModelField):
                raise ModelException(f"Field {field} has bad type")
            #This will raise exception on error
            f.validate()
            with contextlib.suppress(BackendErrorNotFound):
                if f.unique and DatabaseManager.get_backend().load_by_id(self,{field:f.value}):
                    raise ValidateException(f"{field} already exists")
            logger.debug("Add field to update %s",field)
            validated_data[field]=f.value
        self._validated_data = validated_data
        return self._validated_data

    def save(self):
        """Save model using database backend
        """
        if not self._duty_fields:
            raise ModelException(f"Nothing to save")
        if not self._validated_data:
            self.validate()
        logger.debug("[MODEL]Save: %s %s",self,self._validated_data)
        DatabaseManager.get_backend().save(self)
        
    def delete(self):
        """Delete object from database
        """
        logger.debug("[MODEL]Save: %s",self)
        DatabaseManager.get_backend().delete(self)

    def is_new(self):
        """ checks if object newly created

        Returns:
           Bool: new flag
        """
        return self._is_new


    def update(self,field:str,value:str):
        """Updates value in field

        Args:
            field (str): field to update
            value (str): value to set
        """
        if field not in self.__slots__:
            raise ModelException(f"Field {field} connot be updated")

        f = getattr(self,field)
        if not isinstance(f,ModelField):
            raise ModelException(f"{field} has bad type")
        if f.read_only:
            raise ModelException(f"{field} is read only")

        logger.debug("[MODEL]Update field %s",field)
        f.value = value
        self._duty_fields.add(field)


    @classmethod
    def create(cls,**kwargs):
        """Create new model

        Args:
            params (dict): parameters specified to model

        Returns:
            Model: newly created model
        """
        return cls(**kwargs,is_new=True)

    def __iter__(self):
        for f in self.__slots__:
            field = getattr(self,f)
            if field.hidden:
                continue
            yield f, field.value

    def __str__(self):
        return f"{self.__class__.__name__}{self.get_db_key()}"

    #  DBObject implementation
    def get_db_key(self):
        """Return list in format [key,key_value]
        """
        #NOTE: Implement it in delivered class with appropriative values
        raise NotImplementedError

    def get_db_updates(self) -> dict:
        """Returns fields name for create/update operations
        """
        if not self._validated_data:
            raise ModelException('Model not validated. Plase call validate before save')
        logger.debug("[MODEL]Values to update : %s",self._validated_data)
        return self._validated_data