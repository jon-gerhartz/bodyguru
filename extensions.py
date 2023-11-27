from dotenv import load_dotenv
import os
import pandas as pd
import pg8000
from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DBAPIError

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_PW = os.getenv("DB_PW")

url_obj = URL.create(
    "postgresql+pg8000",
    username=DB_USER,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
    password=DB_PW
)

engine = create_engine(url_obj)

Session = sessionmaker(bind=engine)


def execute_query(query, **kwargs):
    session = Session()
    try:
        result = session.execute(text(query), kwargs)
        session.commit()
        return result
    except DBAPIError as e:
        session.rollback()
        print(f"Database error: {e}")
        # Handle error or re-raise
    finally:
        session.close()


def execute_pd(query, *args):
    with Session() as session:
        try:
            result = pd.read_sql(query, session.bind, params=args)
            return result
        except DBAPIError as e:
            print(f"Database error: {e}")
            # Handle error or re-raise
