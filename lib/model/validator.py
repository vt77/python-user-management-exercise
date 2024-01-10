from typing import Protocol

class ValidateException(Exception):
    """Validation error handling exeption"""

class BaseValidator(Protocol):
    def validate(self,value):
        """Validate value according to valiador specification

        Args:
            value (str): value to check

        Raises:
            ValidateException: on validation error
        """
        raise NotImplementedError()


class NamedField(Protocol):
    name:str
    value:any


def is_ascii(s):
    """Check string is ASCII string

    Args:
        s (str): string to check

    Returns:
       bool: True on ok
    """
    return all(ord(c) < 128 for c in s)


class AsciiValidator():
    """Basic ASCII string validator. Implement duck type of Base Validtor"""

    def validate(self,field:NamedField):
        """Validate value according to valiador specification

        Args:
            value (str): value to check

        Raises:
            ValidateException: on validation error
        """

        if not is_ascii(field.value):
            raise ValidateException(f"{field.name} hould be an ASCII string")


class PasswordValidator():
    """Password string validator. Implement duck type of Base Validtor"""

    def validate(self,field:NamedField):
        value = field.value
        if not isinstance(value,str) or not is_ascii(value):
            raise ValidateException(f"{field.name} should be an ASCII string")
        if len(value) < 5 or len(value) > 12:
            raise ValidateException(f"{field.name} should be betwwen 6 and 12 characters length")


class EnumValidator():
    def __init__(self,allowed_values:list):
        self.allowed_values = allowed_values

    def validate(self,field:NamedField):
        value = field.value
        if value not in self.allowed_values:
            raise ValidateException(f"{field.name} should be an one of {self.allowed_values}")
    
class NumberValidator():
    _minval = None
    _maxval = None
    def __init__(self,minval=None,maxval=None):
        self._minval = minval
        self._maxval = maxval

    def validate(self,field:NamedField):
        value = field.value
        if not isinstance(value,int):
            raise ValidateException(f"{field.name} should be a number")
        if self._maxval and value > self._maxval:
            raise ValidateException(f"{field.name} should be maximum {self._maxval}")
        if self._minval and value < self._minval:
            raise ValidateException(f"{field.name} should be minimum {self._minval} {value}")
