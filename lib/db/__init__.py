from abc import ABC

class DbBackend(ABC):
    def save(self,table:str, model:dict):
        """Save entity in database

        Args:
            table (str) : database table 
            model (dict): entity key-value to save
        """
        raise NotImplementedError()

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


class DatabaseManager:

    backend:DbBackend = None

    @classmethod
    def register_backend(cls,backend:DbBackend):
        cls.backend = backend

    @classmethod
    def get_backend(cls) -> DbBackend:
        return cls.backend


class ObjectManager:

    @staticmethod
    def get_one(model,where_clause:dict):
        model_data = DatabaseManager.get_backend().load_by_id(model._table,where_clause)
        return model(**model_data)

    @staticmethod
    def get_many(model,where_clause:dict):
        objects_data = DatabaseManager.get_backend().load_list(model._table, where_clause)
        return [model(**o) for o in objects_data]
