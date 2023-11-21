from dotenv import load_dotenv
import os
import pg8000

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

conn = pg8000.connect(
    user=DB_USER,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)
