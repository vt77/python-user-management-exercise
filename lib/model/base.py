
import logging

from db import DatabaseManager
from model import Model
from .validator import AsciiValidator

class ModelException(Exception):
    """Model error handling exeption"""

logger = logging.getLogger(__name__)


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


class ModelBase(Model):
    
    _is_new = False
    _duty_fields = {}
    _db_table = None

    def __init__(self,is_new=False):
        self._is_new = is_new
        self._duty_fields = self.__slots__ if is_new else {}

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
            if f.unique and DatabaseManager.get_backend().load_by_id(self._db_table,{field:f.value}):
                raise ModelException(f"{field} already exists")
            logger.debug("Add field to update %s",field)
            validated_data[field]=f.value
        return validated_data

    def save(self):
        """Save model using database backend
        """
        validated_data = self.validate()
        if not bool(validated_data):
            raise ModelException("Nothing to save")
        logger.debug("[MODEL]Save: %s",validated_data)
        DatabaseManager.get_backend().save(self._db_table, validated_data)
        
    def delete(self):
        DatabaseManager.get_backend().save(self._db_table, self.get_key())

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
        self._duty_fields[field] = 1


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
