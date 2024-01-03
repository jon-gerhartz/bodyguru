from dotenv import load_dotenv
from migrations.init_db import *
import os
import pg8000

load_dotenv()
DB_USER = os.getenv("DB_USER")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_PW = os.getenv("DB_PW")
INIT_DB_NAME = os.getenv("INIT_DB_NAME")


def create_conn(DB_NAME):
    conn = pg8000.connect(
        user=DB_USER,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        password=DB_PW
    )
    return conn


init_conn = create_conn(INIT_DB_NAME)
init_conn.autocommit = True

with init_conn.cursor() as cur:
    cur.execute(db_exists)
    exists = cur.fetchone()

    if not exists:
        cur.execute(create_db)
        init_conn.commit()
    cur.close()
    init_conn.close()


def run_migrations(conn, run_list):
    try:
        cursor = conn.cursor()
        for i in run_list:
            cursor.execute(i)
        conn.commit()
        message = 'successfully commited migrations'
    except Exception as e:
        message = e
    return message


conn = create_conn(DB_NAME)

run_list = [init_exercise_types, init_muscle_group_name, init_exercise_equipment, init_workout_type, init_exercises, init_workouts, init_users, init_workout_logs,
            init_user_workouts, init_user_exercises, init_user_reports, insert_exercise_types, insert_exercise_equipment,
            insert_muscle_group_names, insert_workout_types, add_link_to_exercises, init_user_status, insert_user_status, add_name_to_users,
            add_status_to_users, add_status_foreign_key, init_password_reset_request]

message = run_migrations(conn, run_list)
print(message)
conn.close()
