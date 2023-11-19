from dotenv import load_dotenv
from migrations.init_db import run_migrations, run_list
import os
import pg8000
import sqlite3
from sqlite3 import Error


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn


DB = os.getenv('DB')
print(DB)

# conn = create_connection(DB)

# message = run_migrations(conn)
# print(message)
