
import logging
from abc import ABC


from db import DatabaseManager, DbObject
from .validator import AsciiValidator

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
    value = None
    validator = None
    read_only = False
    unique = False

    def __init__(self,name:str,value:str=None,validator=None,read_only=False, unique=False):
        self.name = name
        self.value = value
        self.validator = validator
        if not self.validator:
            self.validator = AsciiValidator()
        self.read_only = read_only
        self.unique = unique

    def __str__(self):
        return self.value


    def validate(self):
        if not self.validator:
            raise ModelException("No validator defined for field %s",self.name)
        logger.debug("Validate field %s using %s",self.name,self.validator)
        self.validator.validate(self.value)


class ModelBase(Model,DbObject):
    
    _is_new = False
    _duty_fields = {}

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
            if f.unique and DatabaseManager.get_backend().load_by_id(self,{field:f.value}):
                raise ModelException(f"{field} already exists")
            logger.debug("Add field to update %s",field)
            validated_data[field]=f.value
        return validated_data

    def save(self):
        """Save model using database backend
        """
        if not self._duty_fields:
            raise ModelException(f"Nothing to save")
        logger.debug("[MODEL]Save: %s",self)
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
            raise ModelException(f"Field {field} has bad type")
        if f.read_only:
            raise ModelException(f"Field {field} is read only")

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
            yield f, str(getattr(self,f))

    def __str__(self):
        return f"{self.__class__.__name__}{self.get_db_key()}"

    #  DBObject implementation
    def get_db_key(self):
        """Return list in format [key,key_value]
        """
        #NOTE: Implement it in delivered class with appropriative values
        raise NotImplementedError

    def get_dirty_fields(self) -> dict:
        """Returns fields name for create/update operations
        """
        validated_data = self.validate()
        logger.debug("[MODEL]Values to update : %s",validated_data)
        return validated_data