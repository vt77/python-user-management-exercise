from abc import ABC

class BackendError(Exception):
    """Backend errors"""

class BackendErrorNotFound(BackendError):
    """Backend errors - entry not found"""



class DbObject(ABC):

    """ Name of table """
    _db_table = None

    def get_db_key(self) -> str:
        """Returns key field name (for new object) or key=>vlaue pair for RUD operations
        """
        raise NotImplementedError()

    def get_dirty_fields(self) -> dict:
        """Returns fields name for create/update operations
        """
        raise NotImplementedError()



class DbBackend(ABC):
    def save(self,model:DbObject):
        """Save entity in database

        Args:
            table (str) : database table 
            model (dict): entity key-value to save
        """
        raise NotImplementedError()

    def delete(self,model:DbObject):
        """Delete object from db

        Args:
            model (DbObject): model data
        """

    def load_by_id(self,table:str, id:dict):
        """Load entity by id. 
        
        Note:
            If multiply entity found, only first returned. Use load_list to load multiply entity

        Args:
            table (str) : database table 
            id (dict): key-value for key field

        Returns:
            Model : loaded model or None
        """
        raise NotImplementedError()


    def load_list(self,table:str, filter:dict):
        """Load list of entities

        Args:
            table (str) : database table 
            filter (dict): where clause filter

        Returns:
            List[Model]: List of entities
        """
        raise NotImplementedError()
