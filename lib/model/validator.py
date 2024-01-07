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

    def validate(self,value:str):
        """Validate value according to valiador specification

        Args:
            value (str): value to check

        Raises:
            ValidateException: on validation error
        """

        if not is_ascii(value):
            raise ValidateException("Should be an ASCII string")


class PasswordValidator():
    """Password string validator. Implement duck type of Base Validtor"""

    def validate(self,value:str):
        if not isinstance(value,str) or not is_ascii(value):
            raise ValidateException("should be an ASCII string")
        if len(value) < 6 or len(value) > 12:
            raise ValidateException("should be betwwen 6 and 12 characters length")


class EnumValidator():
    def __init__(self,allowed_values:list):
        self.allowed_values = allowed_values

    def validate(self,value:str):
        if value not in self.allowed_values:
            raise ValidateException(f"should be an one of {self.allowed_values}")
    
