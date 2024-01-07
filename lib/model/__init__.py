from abc import ABC
from .validator import ValidateException
from .base import ModelException

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