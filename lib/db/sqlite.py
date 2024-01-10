import logging
import sqlite3

from . import DbBackend,DbObject,BackendError, BackendErrorNotFound

logger = logging.getLogger(__name__)


class SqLiteBackend(DbBackend):
    def __init__(self,db_path):
        self.connection = sqlite3.connect(db_path,check_same_thread=False)

    def save(self,model:DbObject):
        key, value = model.get_db_key()
        fields_to_save = model.get_db_updates()
        fields_names = fields_to_save.keys()
        params = [str(f)  for f in fields_to_save.values()]
        
        if not value:
            #New object. Insert
            values_placeholder = ",".join(['?'] * len(fields_to_save))
            query = f"INSERT INTO {model._db_table} ({','.join(fields_names)}) VALUES ({values_placeholder})"
        else: 
            # Update object 
            values_placeholder = ','.join([f"{f}=?" for f in fields_names])
            params.append(str(value))
            query = f"UPDATE {model._db_table} SET {values_placeholder} WHERE {key}=?"

        logger.debug("[SQLITE][SAVE]Query: %s : %s",query,params)
        try:
            cursor = self.connection.cursor()
            cursor.execute(query,params)
            self.connection.commit()
        except sqlite3.OperationalError as ex:
            raise BackendError(str(ex))

    def delete(self,model:DbObject):
        key, value = model.get_db_key()
        query = f"DELETE FROM {model._db_table} WHERE {key}=?"
        logger.debug("[SQLITE][DELETE]Query: %s : %s",query,value)
        cursor = self.connection.cursor()
        cursor.execute(query,(value,))

    def load_by_id(self,table:str, record_id:dict):
        key_name,value = record_id.popitem()
        query = f"SELECT * from {table} WHERE {key_name}=?"
        logger.debug("[SQLITE][LOADID]: %s : %s",query,[value])
        cursor = self.connection.cursor()
        res = cursor.execute(query,(value,))
        row = cursor.fetchone()
        if row is None:
            raise BackendErrorNotFound('Not found')
        col_name_list = [field[0] for field in res.description]
        return {c:row[i] for i,c in enumerate(col_name_list)}

    def load_list(self,table:str, where_clause:dict=None):
        query = f"SELECT * from {table}"
        params = ()
        if where_clause:
            where_fields = where_clause.keys()
            where = ' AND '.join([f'{f}=?' for f in where_fields])
            params = tuple(where_clause.values())
            query = query + ' WHERE ' + where

        logger.debug("[SQLITE][SAVE]LoadList: %s : %s",query,params)
        cursor = self.connection.cursor()
        res = cursor.execute(query,params)
        col_name_list = [field[0] for field in res.description]

        def build_row_object(row):
            return {c:row[i] for i,c in enumerate(col_name_list)}

        rows = cursor.fetchall()
        return [build_row_object(o) for o in rows]


    def rotate(self,table:str,max_size:int=100) -> bool:
        """ This is custom function for rotating audits """
        cursor = self.connection.cursor()
        res = cursor.execute(f"SELECT COUNT(*) from {table}")
        count = int(cursor.fetchone()[0])
        if count < max_size:
            return False
        logger.debug("[SQLITE][ROTATE] Found %s count for %s of max %s",count,table,max_size)
        query = f"INSERT INTO {table}_archive select * from {table} ORDER BY datetime DESC LIMIT {max_size},{count}"
        res = cursor.execute(query)
        query = f"DELETE FROM {table} ORDER BY datetime DESC LIMIT {max_size},{count}"
        res = cursor.execute(query)
        return True


def init_database(db_name):
    import os

    if os.path.exists(db_name):
        print(f"[+]Delete file {db_name}")
        os.remove(db_name)
    connection = sqlite3.connect(db_name)
    print("Create users table")
    connection.execute("CREATE TABLE users (username TEXT, password TEXT,gender TEXT,deleted NUMBER)")
    print("Create audit table")
    connection.execute("CREATE TABLE audit (uuid TEXT, username TEXT, message TEXT,datetime NUMBER)")
    print("Create audit_archive table")
    connection.execute("CREATE TABLE audit_archive (uuid TEXT, username TEXT, message TEXT,datetime NUMBER)")

if __name__ == '__main__':
    import sys
    globals()[sys.argv[1]](sys.argv[2])




