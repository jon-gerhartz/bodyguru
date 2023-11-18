from extensions import DB, create_connection
import pandas as pd
from lib.queries import *
import uuid
from datetime import datetime


def get_exercises(user_id=''):
    conn = create_connection(DB)
    q_get_exercises_all_formatted = q_get_exercises_all.format(user_id=user_id)
    df = pd.read_sql_query(q_get_exercises_all_formatted, conn)
    return df


def get_exercise(lookup_val, by_name=False):
    if by_name == True:
        lookup_col = 'name'
    else:
        lookup_col = 'id'
    q_get_exercise_formatted = q_get_exercise.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_exercise_formatted, conn)
    return df


def create_exercise(name, e_type, equipment, description, muscle_group, user_id=''):
    conn = create_connection(DB)
    cur = conn.cursor()
    exercise_id = str(uuid.uuid4())
    cur.execute(q_create_exercise, (exercise_id, name,
                e_type, equipment, description, muscle_group))
    if user_id != '':
        cur.execute(q_create_user_exercise, (user_id, exercise_id))
    conn.commit()
    return 'done'


def delete_exercise_item(exercise_id):
    conn = create_connection(DB)
    cur = conn.cursor()
    q_delete_exercise_formatted = q_delete_exercise.format(
        exercise_id=exercise_id)
    cur.execute(q_delete_exercise_formatted)
    conn.commit()
    return 'exercise deleted'


# crud functions for workout object
def get_workouts(user_id=''):
    conn = create_connection(DB)
    q_get_workouts_all_formatted = q_get_workouts_all.format(user_id=user_id)
    df = pd.read_sql_query(q_get_workouts_all_formatted, conn)
    return df


def get_workout(lookup_val, by_name=False):
    conn = create_connection(DB)
    if by_name == True:
        lookup_col = 'name'
    else:
        lookup_col = 'id'
    q_get_workout_formatted = q_get_workout.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    df = pd.read_sql_query(q_get_workout_formatted, conn)
    return df


def create_workout(workout_name, w_type, description, workout_data, user_id=''):
    conn = create_connection(DB)
    cur = conn.cursor()
    workout_id = str(uuid.uuid4())
    cur.execute(q_create_workout, (workout_id, workout_name,
                w_type, description, workout_data))
    if user_id != '':
        cur.execute(q_create_user_workout, (user_id, workout_id))
    conn.commit()
    return 'done'


def delete_workout_item(workout_id):
    conn = create_connection(DB)
    cur = conn.cursor()
    q_delete_workout_formatted = q_delete_workout.format(
        workout_id=workout_id)
    cur.execute(q_delete_workout_formatted)
    conn.commit()
    return 'workout deleted'

# crud functions for workout_logs object


def get_workout_logs(user_id):
    q_get_workout_logs_all_formatted = q_get_workout_logs_all.format(
        user_id=user_id)
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_workout_logs_all_formatted, conn)
    return df


def get_workout_log(log_id):
    q_get_workout_log_formatted = q_get_workout_log.format(id=log_id)
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_workout_log_formatted, conn)
    return df


def create_workout_log(workout_id, user_id, feedback_data, past_date=''):
    log_id = str(uuid.uuid4())
    created_at = datetime.now()
    if past_date == '':
        completed_at = datetime.now()
    else:

        dt_obj = datetime.strptime(past_date, "%Y-%m-%dT%H:%M")
        fmtd_dt = dt_obj.strftime("%Y-%m-%d %H:%M:00.000000")
        completed_at = fmtd_dt
    conn = create_connection(DB)
    cur = conn.cursor()
    cur.execute(q_create_workout_log, (
        log_id, workout_id, user_id, feedback_data, created_at, completed_at))
    conn.commit()
    return 'done'


def delete_workout_log_item(log_id):
    conn = create_connection(DB)
    cur = conn.cursor()
    q_delete_workout_log_formatted = q_delete_workout_log.format(
        log_id=log_id)
    cur.execute(q_delete_workout_log_formatted)
    conn.commit()
    return 'workout log deleted'

# crud functions for user


def create_user(email, password_hash):
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    conn = create_connection(DB)
    cur = conn.cursor()
    cur.execute(q_create_user, (user_id, email, password_hash, created_at))
    conn.commit()
    return user_id


def get_user(lookup_val, by_email=False):
    if by_email:
        lookup_col = 'email'
    else:
        lookup_col = 'id'
    q_get_user_formatted = q_get_user.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_user_formatted, conn)
    return df


def get_user_auth(email):
    q_get_user_auth_formatted = q_get_user_auth.format(email=email)
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_user_auth_formatted, conn)
    return df

# crud functions for dropdown lookup


def get_muscle_groups():
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_muscle_groups_all, conn)
    return df


def get_exercise_types():
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_exercise_types_all, conn)
    return df


def get_exercise_equipment():
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_exercise_equipment_all, conn)
    return df


def get_workout_types():
    conn = create_connection(DB)
    df = pd.read_sql_query(q_get_workout_types_all, conn)
    return df
