from extensions import execute_query, execute_pd, Session
import pandas as pd
from lib.queries import *
import uuid
from datetime import datetime
from sqlalchemy import bindparam, text


def get_exercises(user_id=''):
    q_get_exercises_all_formatted = q_get_exercises_all.format(user_id=user_id)
    df = execute_pd(q_get_exercises_all_formatted)
    return df


def get_exercises_fp(user_id=''):
    q_get_exercises_fp_users_formatted = q_get_exercises_fp_users.format(
        user_id=user_id)
    df = execute_pd(q_get_exercises_fp_users_formatted)
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

def update_exercise_details(exercise_id, description):
    execute_query(q_update_exercise_details, id=exercise_id, description=description)
    return 'updated'


def update_exercise_video(exercise_id, video_slug):
    execute_query(q_update_exercise_video, id=exercise_id, video_slug=video_slug)
    return 'updated'


def get_exercises_admin():
    df = execute_pd(q_get_exercises_admin)
    return df


# crud functions for workout object
def get_workouts(user_id=''):
    q_get_workouts_all_formatted = q_get_workouts_all.format(user_id=user_id)
    df = execute_pd(q_get_workouts_all_formatted)
    return df


def get_workout(lookup_val, by_name=False, user_id=''):
    if by_name == True:
        lookup_col = 'name'
    else:
        lookup_col = 'id'
    q_get_workout_formatted = q_get_workout.format(
        lookup_col=lookup_col, lookup_val=lookup_val, user_id=user_id)
    df = execute_pd(q_get_workout_formatted)
    return df


def get_workout_raw(workout_id):
    q_get_workout_raw_formatted = q_get_workout_raw.format(workout_id=workout_id)
    df = execute_pd(q_get_workout_raw_formatted)
    return df


def create_workout(workout_name, w_type, description, workout_data, user_id=''):
    workout_id = str(uuid.uuid4())
    execute_query(q_create_workout, id=workout_id, name=workout_name,
                  workout_type_id=w_type, description=description, workout_data=workout_data)
    if user_id != '':
        execute_query(q_create_user_workout,
                      user_id=user_id, workout_id=workout_id)
    return workout_id


def delete_workout_item(workout_id):
    q_delete_workout_formatted = q_delete_workout.format(
        workout_id=workout_id)
    execute_query(q_delete_workout_formatted)
    return 'workout deleted'


def update_workout_data(workout_id, workout_data):
    execute_query(q_update_workout_data, id=workout_id, workout_data=workout_data)
    return 'updated'


def update_workout_meta(workout_id, name, description):
    execute_query(q_update_workout_meta, id=workout_id, name=name, description=description)
    return 'updated'


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


def create_workout_log(workout_id, user_id, feedback_data, past_date='', completed_at_value='__auto__'):
    log_id = str(uuid.uuid4())
    created_at = datetime.now()
    if completed_at_value != '__auto__':
        completed_at = completed_at_value
    elif past_date == '':
        completed_at = datetime.now()
    else:

        dt_obj = datetime.strptime(past_date, "%Y-%m-%dT%H:%M")
        completed_at = dt_obj.strftime('%Y-%m-%dT%H:%M:%S.%f')
    execute_query(q_create_workout_log, id=log_id, workout_id=workout_id,
                  user_id=user_id, feedback_data=feedback_data, created_at=created_at, completed_at=completed_at)
    return log_id


def get_workout_logs_for_workout_user(user_id, workout_id, limit=10):
    limit_val = int(limit) if str(limit).isdigit() else 10
    q_get_workout_logs_formatted = q_get_workout_logs_for_workout_user.format(
        user_id=user_id, workout_id=workout_id, limit=limit_val)
    df = execute_pd(q_get_workout_logs_formatted)
    return df


def update_workout_log(log_id, feedback_data, completed_at=None):
    execute_query(q_update_workout_log, id=log_id, feedback_data=feedback_data, completed_at=completed_at)
    return 'updated'


def delete_workout_log_item(log_id):
    q_delete_workout_log_formatted = q_delete_workout_log.format(
        log_id=log_id)
    execute_query(q_delete_workout_log_formatted)
    return 'workout log deleted'


# crud functions for user
def create_user(email, name, password_hash, status_id=1):
    user_id = str(uuid.uuid4())
    created_at = datetime.now()
    execute_query(q_create_user, id=user_id, email=email,
                  password_hash=password_hash, created_at=created_at,
                  name=name, status_id=status_id)

    execute_query(q_set_user_preferences, user_id=user_id,
                  show_all_workouts=False)

    return user_id


def update_pass(user_id, password_hash):
    execute_query(q_update_user,
                  id=user_id, password_hash=password_hash)
    return 'user updated'


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


def get_user_preferences(user_id):
    q_get_user_preferences_formatted = q_get_user_preferences.format(
        user_id=user_id)
    df = execute_pd(q_get_user_preferences_formatted)
    return df


def get_user_by_email(email):
    q_get_user_by_email_formatted = q_get_user_by_email.format(email=email)
    df = execute_pd(q_get_user_by_email_formatted)
    return df


def get_user_exercise_ids(user_id):
    q_get_user_exercise_ids_formatted = q_get_user_exercise_ids.format(user_id=user_id)
    df = execute_pd(q_get_user_exercise_ids_formatted)
    return df


def get_exercise_ids_by_names(names):
    if not names:
        return pd.DataFrame(columns=["id", "name"])
    stmt = text(q_get_exercise_ids_by_names).bindparams(bindparam("names", expanding=True))
    with Session() as session:
        result = session.execute(stmt, {"names": list(names)})
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=["id", "name"])


def add_user_exercise(user_id, exercise_id):
    execute_query(q_create_user_exercise, user_id=user_id, exercise_id=exercise_id)
    return 'done'


def create_workout_share(sender_user_id, receiver_user_id, workout_snapshot, status='pending'):
    share_id = str(uuid.uuid4())
    created_at = datetime.now()
    execute_query(
        q_create_workout_share,
        id=share_id,
        sender_user_id=sender_user_id,
        receiver_user_id=receiver_user_id,
        workout_snapshot=workout_snapshot,
        status=status,
        created_at=created_at
    )
    return share_id


def create_workout_email_invite(sender_user_id, recipient_email, workout_snapshot, status='pending'):
    invite_id = str(uuid.uuid4())
    invite_token = str(uuid.uuid4())
    created_at = datetime.now()
    execute_query(
        q_create_workout_email_invite,
        id=invite_id,
        sender_user_id=sender_user_id,
        recipient_email=recipient_email,
        invite_token=invite_token,
        workout_snapshot=workout_snapshot,
        status=status,
        created_at=created_at
    )
    return invite_token


def get_workout_email_invite_by_token(invite_token):
    q_get_workout_email_invite_by_token_formatted = q_get_workout_email_invite_by_token.format(
        invite_token=invite_token)
    df = execute_pd(q_get_workout_email_invite_by_token_formatted)
    return df


def accept_workout_email_invite(invite_id, accepted_user_id):
    execute_query(
        q_accept_workout_email_invite,
        id=invite_id,
        status='accepted',
        accepted_at=datetime.now(),
        accepted_user_id=accepted_user_id
    )
    return 'updated'


def get_pending_workout_shares(user_id):
    q_get_pending_workout_shares_formatted = q_get_pending_workout_shares.format(user_id=user_id)
    df = execute_pd(q_get_pending_workout_shares_formatted)
    return df


def get_workout_share(share_id):
    q_get_workout_share_formatted = q_get_workout_share.format(share_id=share_id)
    df = execute_pd(q_get_workout_share_formatted)
    return df


def update_workout_share_status(share_id, status, accepted_workout_id=None):
    execute_query(
        q_update_workout_share_status,
        id=share_id,
        status=status,
        responded_at=datetime.now(),
        accepted_workout_id=accepted_workout_id
    )
    return 'updated'

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

# workout exercise lookup
def get_exercises_by_names(names):
    if not names:
        return pd.DataFrame(columns=["id", "name", "video_slug"])
    stmt = text(q_get_exercises_by_names).bindparams(bindparam("names", expanding=True))
    with Session() as session:
        result = session.execute(stmt, {"names": list(names)})
        rows = result.fetchall()
        return pd.DataFrame(rows, columns=["id", "name", "video_slug"])

# crud functions for password reset


def create_pass_reset_request(user_id, url_var):
    created_at = datetime.now()
    execute_query(q_create_pass_reset_request,
                  user_id=user_id, url_var=url_var, created_at=created_at)


def get_pass_reset_user(url_var):
    q_get_pass_reset_user_formatted = q_get_pass_reset_user.format(
        url_var=url_var)
    df = execute_pd(q_get_pass_reset_user_formatted)
    return df
