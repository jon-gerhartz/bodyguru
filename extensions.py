from dotenv import load_dotenv
import os
import pandas as pd
import pg8000
from sqlalchemy import create_engine, URL, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import DBAPIError
import time

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

engine = create_engine(url_obj, pool_pre_ping=True, pool_recycle=1800)

Session = sessionmaker(bind=engine)

MAX_RETRIES = 3
RETRY_BACKOFF = 2  # Seconds


def execute_query(query, **kwargs):
    for attempt in range(MAX_RETRIES):
        session = Session()
        try:
            result = session.execute(text(query), kwargs)
            session.commit()
            return result
        except DBAPIError as e:
            session.rollback()
            print(f"Attempt {attempt + 1} failed with error: {e}")
            time.sleep(RETRY_BACKOFF ** attempt)
            if attempt == MAX_RETRIES - 1:
                raise e
        finally:
            session.close()


def execute_pd(query, *args):
    for attempt in range(MAX_RETRIES):
        with Session() as session:
            try:
                result = pd.read_sql(query, session.bind, params=args)
                return result
            except DBAPIError as e:
                session.rollback()
                print(f"Attempt {attempt + 1} failed with error: {e}")
                time.sleep(RETRY_BACKOFF ** attempt)
                if attempt == MAX_RETRIES - 1:
                    raise e
