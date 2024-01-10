from abc import ABC
from typing import Type
from . import DbBackend,DbObject

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
    def get_one(model:Type[DbObject],where_clause:dict):
        model_data = DatabaseManager.get_backend().load_by_id(model._db_table, where_clause)
        return model(**model_data)

    @staticmethod
    def get_many(model:Type[DbObject],where_clause:dict=None,order=None):
        # TODO: order not supported yet
        objects_data = DatabaseManager.get_backend().load_list(model._db_table, where_clause)
        return [model(**o) for o in objects_data]

