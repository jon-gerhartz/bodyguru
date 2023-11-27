from extensions import execute_query, execute_pd
import pandas as pd
from lib.queries import *
import uuid
from datetime import datetime


def get_exercises(user_id=''):
    q_get_exercises_all_formatted = q_get_exercises_all.format(user_id=user_id)
    df = execute_pd(q_get_exercises_all_formatted)
    return df


def get_exercise(lookup_val, by_name=False):
    if by_name == True:
        lookup_col = 'name'
    else:
        lookup_col = 'id'
    q_get_exercise_formatted = q_get_exercise.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    df = execute_pd(q_get_exercise_formatted)
    return df


def create_exercise(name, e_type, equipment, description, muscle_group, user_id=''):
    exercise_id = str(uuid.uuid4())
    execute_query(q_create_exercise, id=exercise_id, name=name,
                  exercise_type_id=e_type, exercise_equipment_id=equipment, description=description, muscle_group_id=muscle_group)
    if user_id != '':
        execute_query(q_create_user_exercise, user_id=user_id,
                      exercise_id=exercise_id)
    return 'done'


def delete_exercise_item(exercise_id):
    q_delete_exercise_formatted = q_delete_exercise.format(
        exercise_id=exercise_id)
    execute_query(q_delete_exercise_formatted)
    return 'exercise deleted'


# crud functions for workout object
def get_workouts(user_id=''):
    q_get_workouts_all_formatted = q_get_workouts_all.format(user_id=user_id)
    df = execute_pd(q_get_workouts_all_formatted)
    return df


def get_workout(lookup_val, by_name=False):
    if by_name == True:
        lookup_col = 'name'
    else:
        lookup_col = 'id'
    q_get_workout_formatted = q_get_workout.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    df = execute_pd(q_get_workout_formatted)
    return df


def create_workout(workout_name, w_type, description, workout_data, user_id=''):
    workout_id = str(uuid.uuid4())
    execute_query(q_create_workout, id=workout_id, name=workout_name,
                  workout_type_id=w_type, description=description, workout_data=workout_data)
    if user_id != '':
        execute_query(q_create_user_workout,
                      user_id=user_id, workout_id=workout_id)
    return 'done'


def delete_workout_item(workout_id):
    q_delete_workout_formatted = q_delete_workout.format(
        workout_id=workout_id)
    execute_query(q_delete_workout_formatted)
    return 'workout deleted'


# crud functions for workout_logs object
def get_workout_logs(user_id):
    q_get_workout_logs_all_formatted = q_get_workout_logs_all.format(
        user_id=user_id)
    df = execute_pd(q_get_workout_logs_all_formatted)
    return df


def get_workout_log(log_id):
    q_get_workout_log_formatted = q_get_workout_log.format(id=log_id)
    df = execute_pd(q_get_workout_log_formatted)
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
    execute_query(q_create_workout_log, id=log_id, workout_id=workout_id,
                  user_id=user_id, feedback_data=feedback_data, created_at=created_at, completed_at=completed_at)
    return 'done'


def delete_workout_log_item(log_id):
    q_delete_workout_log_formatted = q_delete_workout_log.format(
        log_id=log_id)
    execute_query(q_delete_workout_log_formatted)
    return 'workout log deleted'

# crud functions for user


def create_user(email, password_hash):
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    execute_query(q_create_user, id=user_id, email=email,
                  password_hash=password_hash, created_at=created_at)
    return user_id


def get_user(lookup_val, by_email=False):
    if by_email:
        lookup_col = 'email'
    else:
        lookup_col = 'id'
    q_get_user_formatted = q_get_user.format(
        lookup_col=lookup_col, lookup_val=lookup_val)
    df = execute_pd(q_get_user_formatted)
    return df


def get_user_auth(email):
    q_get_user_auth_formatted = q_get_user_auth.format(email=email)
    df = execute_pd(q_get_user_auth_formatted)
    return df

# crud functions for dropdown lookup


def get_muscle_groups():
    df = execute_pd(q_get_muscle_groups_all)
    return df


def get_exercise_types():
    df = execute_pd(q_get_exercise_types_all)
    return df


def get_exercise_equipment():
    df = execute_pd(q_get_exercise_equipment_all)
    return df


def get_workout_types():
    df = execute_pd(q_get_workout_types_all)
    return df
