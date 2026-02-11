from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort, Response, stream_with_context
from exp.landing import landing_data
import json
import re
from lib.crud import *
from lib.data_meta import *
from lib.reports import run_report_flow
from utils.app_functions import auth_required
import os
from werkzeug.utils import secure_filename
from utils.storage import get_storage_config, get_s3_client, get_bucket_name, presign_get_url
from openai import OpenAI
from datetime import datetime

# Allowed video extensions for upload endpoint
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm', 'mkv'}


def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    if 'authenticated' not in session.keys():
        session['authenticated'] = False

    if session['authenticated'] == True:
        user_id = session['user_id']
        return redirect(url_for('main.dashboard', user_id=user_id))
    return render_template('index.html')


@main.route('/dash/<user_id>', methods=['GET', 'POST'])
@auth_required
def dashboard(user_id):
    user = get_user(user_id)
    logs = get_workout_logs(user_id)
    files = run_report_flow(logs, user_id)
    return render_template('dashboard.html', user=user, logs=logs, files=files)


@main.route('/library', methods=['GET', 'POST'])
@auth_required
def library():
    user_id = session['user_id']
    if request.method == 'GET':
        show_all_workouts = session['show_all_workouts']
        if show_all_workouts == 'TRUE':
            exercises = get_exercises_fp(user_id=user_id)
        else:
            exercises = get_exercises(user_id=user_id)
        col_data = create_filer_col_dict(exercise_filter_cols, exercises)
        return render_template('library.html', exercises=exercises, data_cols=exercise_filter_cols, col_data=col_data)
    else:
        name = request.form.get('name')
        e_type = request.form.get('etype')
        equipment = request.form.get('equipment')
        description = request.form.get('description')
        muscle_group = request.form.get('muscle_group')
        create_exercise(name, e_type, equipment, description,
                        muscle_group, user_id=user_id)
        return redirect(url_for('main.library'))


@main.route('/exercises', methods=['GET'])
@auth_required
def exercises():
    user_id = session['user_id']
    exercises_df = get_exercises(user_id)
    exercises_list = exercises_df.to_dict(orient='records')
    exercises_dict = {'name': 'exercise', 'data': exercises_list}
    return exercises_dict


@main.route('/exercise-details/<exercise_id>', methods=['GET', 'POST'])
@auth_required
def details(exercise_id):
    if request.method == 'POST':
        description = request.form.get('description')
        update_exercise_details(exercise_id, description)
        flash("Exercise successfully updated")
        return redirect(url_for('main.details', exercise_id=exercise_id))

    exercise = get_exercise(exercise_id)
    return render_template('exercise_details.html', exercise=exercise)


@main.route('/delete-exercise/<exercise_id>', methods=['POST'])
@auth_required
def delete_exercise(exercise_id):
    resp = delete_exercise_item(exercise_id)
    return redirect(url_for('main.library'))


@main.route('/upload-video', methods=['POST'])
def upload_video():
    provided_key = request.headers.get('X-API-KEY')
    expected_key = current_app.config.get('UPLOAD_API_KEY')
    if not expected_key or provided_key != expected_key:
        abort(401)

    if 'file' not in request.files:
        return {'error': 'No file part in request'}, 400
    file = request.files['file']
    if file.filename == '':
        return {'error': 'No file selected'}, 400
    if not allowed_video_file(file.filename):
        return {'error': 'Invalid video type. Allowed: ' + ', '.join(ALLOWED_VIDEO_EXTENSIONS)}, 400
    filename = secure_filename(file.filename)
    storage_config = get_storage_config()
    s3_client = get_s3_client(storage_config)
    bucket_name = get_bucket_name(storage_config)
    object_key = f"workout_content/{filename}"
    s3_client.put_object(
        Bucket=bucket_name,
        Key=object_key,
        Body=file.stream,
        ContentType=file.mimetype or "application/octet-stream",
    )
    return {'message': 'Video uploaded successfully', 'filename': filename}, 201


@main.route('/video/<path:filename>', methods=['GET'])
@auth_required
def video(filename):
    storage_config = get_storage_config()
    s3_client = get_s3_client(storage_config)
    bucket_name = get_bucket_name(storage_config)
    object_key = f"workout_content/{filename}"
    presigned_url = presign_get_url(
        s3_client,
        bucket_name,
        object_key,
        storage_config.presign_expires_seconds,
    )
    return redirect(presigned_url)


@main.route('/musclegroups', methods=['GET'])
@auth_required
def muscle_groups():
    muscle_groups = get_muscle_groups()
    muscle_groups_list = muscle_groups.to_dict(orient='records')
    muscle_groups_dict = {'name': 'muscle group', 'data': muscle_groups_list}
    return muscle_groups_dict


@main.route('/exercisetypes', methods=['GET'])
@auth_required
def exercise_types():
    exercise_types = get_exercise_types()
    exercise_types_list = exercise_types.to_dict(orient='records')
    exercise_types_dict = {
        'name': 'exercise type', 'data': exercise_types_list}
    return exercise_types_dict


@main.route('/exerciseequipment', methods=['GET'])
@auth_required
def exercise_equipment():
    exercise_equipment = get_exercise_equipment()
    exercise_equipment_list = exercise_equipment.to_dict(orient='records')
    exercise_equipment_dict = {'data': exercise_equipment_list}
    return exercise_equipment_dict


@main.route('/workouttypes', methods=['GET'])
@auth_required
def workout_types():
    workout_types_df = get_workout_types()
    workout_types_list = workout_types_df.to_dict(orient='records')
    workout_types_dict = {'name': 'workout type', 'data': workout_types_list}
    return workout_types_dict


@main.route('/workouts', methods=['GET', 'POST'])
@auth_required
def workouts():
    user_id = session['user_id']
    if request.method == 'GET':
        workouts_df = get_workouts(user_id=user_id)
        if 'shared_from_name' in workouts_df.columns:
            workouts_df['shared_from_name'] = workouts_df['shared_from_name'].fillna('')
        col_data = create_filer_col_dict(workout_filter_cols, workouts_df)
        return render_template('workouts.html', workouts=workouts_df, data_cols=workout_filter_cols, col_data=col_data)
    else:
        name = request.form.get('name')
        w_type = request.form.get('type')
        description = request.form.get('description')
        workout_data = request.form.get('workout_data')
        create_workout(name, w_type, description,
                       workout_data, user_id=user_id)
        return redirect(url_for('main.workouts'))


@main.route('/create-workout-builder', methods=['POST'])
@auth_required
def create_workout_builder():
    payload = request.get_json(silent=True) or {}
    name = (payload.get('name') or 'New Rad Workout').strip()
    description = (payload.get('description') or '').strip()
    workout_type_id = payload.get('workout_type_id')
    sets = payload.get('sets') or []
    if not workout_type_id:
        return {'error': 'Workout type is required.'}, 400
    if not isinstance(sets, list) or len(sets) == 0:
        return {'error': 'At least one set is required.'}, 400

    workout_data = {}
    for idx, set_obj in enumerate(sets, start=1):
        if not isinstance(set_obj, dict):
            continue
        set_name = (set_obj.get('name') or f"Set {idx}").strip()
        exercises = set_obj.get('exercises') or []
        if not isinstance(exercises, list):
            continue
        cleaned = [str(item).strip()
                   for item in exercises if str(item).strip()]
        if cleaned:
            workout_data[set_name] = cleaned

    if not workout_data:
        return {'error': 'Sets must include exercises.'}, 400

    user_id = session['user_id']
    workout_id = create_workout(
        name,
        workout_type_id,
        description,
        json.dumps(workout_data),
        user_id=user_id,
    )
    return {'workout_id': workout_id}, 201


@main.route('/workout-details/<workout_id>', methods=['GET', 'POST'])
@auth_required
def workout_details(workout_id):
    workout = get_workout(workout_id, user_id=session['user_id'])
    if 'shared_from_name' in workout.columns:
        workout['shared_from_name'] = workout['shared_from_name'].fillna('')
    workout_data_str = workout['workout_data'][0]
    workout_data = json.loads(workout_data_str)
    exercise_names = []
    for set_key in workout_data:
        for exercise_name in workout_data[set_key]:
            if exercise_name not in exercise_names:
                exercise_names.append(exercise_name)
    exercise_df = get_exercises_by_names(exercise_names)
    exercise_lookup = dict(zip(exercise_df["name"], exercise_df["video_slug"]))
    return render_template(
        'workout_details.html',
        workout=workout,
        workout_data=workout_data,
        exercise_lookup=exercise_lookup
    )


@main.route('/update-workout/<workout_id>', methods=['POST'])
@auth_required
def update_workout(workout_id):
    workout = get_workout(workout_id, user_id=session['user_id'])
    if workout['is_default_workout'][0] == 1:
        flash("Default workouts cannot be edited.")
        return redirect(url_for('main.workout_details', workout_id=workout_id))

    name = (request.form.get('name') or '').strip()
    description = (request.form.get('description') or '').strip()
    raw_data = request.form.get('workout_data', '')
    try:
        parsed = json.loads(raw_data) if raw_data else {}
    except json.JSONDecodeError:
        flash("Workout data is invalid JSON.")
        return redirect(url_for('main.workout_details', workout_id=workout_id))

    if not isinstance(parsed, dict):
        flash("Workout data must be a JSON object.")
        return redirect(url_for('main.workout_details', workout_id=workout_id))

    cleaned = {}
    for key, value in parsed.items():
        set_name = str(key).strip()
        if not set_name:
            continue
        if not isinstance(value, list):
            continue
        exercises = [str(item).strip() for item in value if str(item).strip()]
        if exercises:
            cleaned[set_name] = exercises

    if not cleaned:
        flash("Workout must include at least one set with exercises.")
        return redirect(url_for('main.workout_details', workout_id=workout_id))

    if name:
        update_workout_meta(workout_id, name, description)
    update_workout_data(workout_id, json.dumps(cleaned))
    flash("Workout updated.")
    return redirect(url_for('main.workout_details', workout_id=workout_id))


@main.route('/get_workout/<workout_id>', methods=['GET'])
@auth_required
def workout_json(workout_id):
    workout = get_workout(workout_id, user_id=session['user_id'])
    workout['workout_data_json'] = workout['workout_data'].apply(json.loads)
    workout_list = workout.to_dict(orient='records')
    workout_dict = {'name': 'workout', 'data': workout_list}
    return workout_dict


@main.route('/get_workouts', methods=['GET'])
@auth_required
def get_workouts_json():
    user_id = session['user_id']
    workouts = get_workouts(user_id=user_id)
    workouts['workout_data_json'] = workouts['workout_data'].apply(json.loads)
    workouts_list = workouts.to_dict(orient='records')
    workouts_dict = {'name': 'workout', 'data': workouts_list}
    return workouts_dict


@main.route('/delete_workout/<workout_id>', methods=['POST'])
@auth_required
def delete_workout(workout_id):
    resp = delete_workout_item(workout_id)
    return redirect(url_for('main.workouts'))


@main.route('/workouts/share', methods=['POST'])
@auth_required
def share_workout():
    user_id = session['user_id']
    workout_id = (request.form.get('workout_id') or '').strip()
    email = (request.form.get('email') or '').strip().lower()
    if not workout_id or not email:
        flash("If that email exists, a share request was sent.")
        return redirect(request.referrer or url_for('main.workouts'))

    receiver_df = get_user_by_email(email)
    if receiver_df.empty:
        flash("If that email exists, a share request was sent.")
        return redirect(request.referrer or url_for('main.workouts'))

    receiver_id = receiver_df['id'].iloc[0]
    if receiver_id == user_id:
        flash("If that email exists, a share request was sent.")
        return redirect(request.referrer or url_for('main.workouts'))

    workout_raw_df = get_workout_raw(workout_id)
    workout_display_df = get_workout(workout_id, user_id=user_id)
    if workout_raw_df.empty or workout_display_df.empty:
        flash("If that email exists, a share request was sent.")
        return redirect(request.referrer or url_for('main.workouts'))

    workout_snapshot = {
        'name': workout_raw_df['name'].iloc[0],
        'description': workout_raw_df['description'].iloc[0] or '',
        'workout_type_id': workout_raw_df['workout_type_id'].iloc[0],
        'type_name': workout_display_df['type'].iloc[0],
        'workout_data': json.loads(workout_raw_df['workout_data'].iloc[0])
    }

    create_workout_share(
        sender_user_id=user_id,
        receiver_user_id=receiver_id,
        workout_snapshot=json.dumps(workout_snapshot),
        status='pending'
    )

    flash("If that email exists, a share request was sent.")
    return redirect(request.referrer or url_for('main.workouts'))


@main.route('/notifications', methods=['GET'])
@auth_required
def notifications():
    user_id = session['user_id']
    pending_df = get_pending_workout_shares(user_id)
    shares = []
    if not pending_df.empty:
        for _, row in pending_df.iterrows():
            snapshot_raw = row['workout_snapshot'] or '{}'
            try:
                snapshot = json.loads(snapshot_raw)
            except json.JSONDecodeError:
                snapshot = {}
            shares.append({
                'id': row['id'],
                'sender_name': row.get('sender_name') or 'Friend',
                'sender_email': row.get('sender_email'),
                'workout_name': snapshot.get('name') or 'Shared workout',
                'workout_type': snapshot.get('type_name') or '',
                'description': snapshot.get('description') or ''
            })
    return render_template('notifications.html', shares=shares)


@main.route('/workouts/share/<share_id>/accept', methods=['POST'])
@auth_required
def accept_workout_share(share_id):
    user_id = session['user_id']
    share_df = get_workout_share(share_id)
    if share_df.empty:
        flash("Share request not found.")
        return redirect(url_for('main.notifications'))

    share = share_df.iloc[0]
    if share['receiver_user_id'] != user_id or share['status'] != 'pending':
        flash("Share request not available.")
        return redirect(url_for('main.notifications'))

    try:
        snapshot = json.loads(share['workout_snapshot'] or '{}')
    except json.JSONDecodeError:
        snapshot = {}

    workout_data = snapshot.get('workout_data') or {}
    workout_data_json = json.dumps(workout_data) if isinstance(workout_data, dict) else snapshot.get('workout_data', '{}')
    new_workout_id = create_workout(
        snapshot.get('name') or 'Shared Workout',
        snapshot.get('workout_type_id'),
        snapshot.get('description') or '',
        workout_data_json,
        user_id=user_id
    )

    exercise_names = _extract_exercise_names_from_workout_data(workout_data if isinstance(workout_data, dict) else {})
    if exercise_names:
        exercise_df = get_exercise_ids_by_names(exercise_names)
        receiver_exercise_df = get_user_exercise_ids(user_id)
        existing_ids = set(receiver_exercise_df['exercise_id'].tolist()) if not receiver_exercise_df.empty else set()
        for _, row in exercise_df.iterrows():
            exercise_id = row['id']
            if exercise_id not in existing_ids:
                add_user_exercise(user_id, exercise_id)
                existing_ids.add(exercise_id)

    update_workout_share_status(share_id, 'accepted', accepted_workout_id=new_workout_id)
    flash("Workout added to your list.")
    return redirect(url_for('main.workouts'))


@main.route('/workouts/share/<share_id>/decline', methods=['POST'])
@auth_required
def decline_workout_share(share_id):
    user_id = session['user_id']
    share_df = get_workout_share(share_id)
    if share_df.empty:
        flash("Share request not found.")
        return redirect(url_for('main.notifications'))
    share = share_df.iloc[0]
    if share['receiver_user_id'] != user_id or share['status'] != 'pending':
        flash("Share request not available.")
        return redirect(url_for('main.notifications'))
    update_workout_share_status(share_id, 'declined', accepted_workout_id=None)
    flash("Share request declined.")
    return redirect(url_for('main.notifications'))


@main.route('/log', methods=['GET', 'POST'])
@auth_required
def logs():
    user_id = session['user_id']
    if request.method == 'GET':
        logs_df = get_workout_logs(user_id)
        col_data = create_filer_col_dict(log_filter_cols, logs_df)
        return render_template('log.html', logs=logs_df, data_cols=log_filter_cols, col_data=col_data)
    else:
        workout_id = request.form.get('workout_id')
        feedback_data = request.form.get('workout_data')
        if 'past_date' in request.form.keys():
            past_date = request.form.get('past_date')
            create_workout_log(workout_id, user_id,
                               feedback_data, past_date=past_date)
        else:
            create_workout_log(workout_id, user_id, feedback_data)
        return redirect(url_for('main.logs'))


@main.route('/log-details/<log_id>', methods=['GET'])
@auth_required
def log_details(log_id):
    log = get_workout_log(log_id)
    log['feedback_data_json'] = log['feedback_data'].apply(json.loads)
    return render_template('log_details.html', log=log)


@main.route('/delete_log/<log_id>', methods=['POST'])
@auth_required
def delete_log(log_id):
    delete_workout_log_item(log_id)
    return redirect(url_for('main.logs'))


@main.route('/join/<var>', methods=['GET', 'POST'])
def landing(var):
    if request.method == 'GET':
        return render_template('landing.html', data=landing_data)
    else:
        return redirect(url_for('main.dashboard'))


def _serialize_df(df, fields=None, limit=50):
    if df is None or df.empty:
        return []
    safe_df = df.head(limit)
    records = safe_df.to_dict(orient='records')
    if fields:
        return [{field: record.get(field) for field in fields} for record in records]
    return records


def _build_assistant_context(user_id):
    workouts_df = get_workouts(user_id=user_id)
    if not workouts_df.empty and 'workout_data' in workouts_df.columns:
        workouts_df = workouts_df.copy()
        workouts_df['workout_data_json'] = workouts_df['workout_data'].apply(
            lambda val: json.loads(val) if val else {}
        )
    workouts = _serialize_df(
        workouts_df,
        fields=['id', 'name', 'type', 'description', 'workout_data_json'],
        limit=30
    )
    logs_df = get_workout_logs(user_id)
    logs = _serialize_df(
        logs_df,
        fields=['id', 'workout_name', 'feedback_data',
                'completed_at', 'created_at'],
        limit=30
    )
    exercises_df = get_exercises(user_id=user_id)
    exercises = _serialize_df(
        exercises_df,
        fields=['id', 'name', 'type', 'equipment', 'muscle_group_name'],
        limit=40
    )
    return {
        'workouts': workouts,
        'workout_logs': logs,
        'exercises': exercises
    }


def _extract_exercise_names_from_workout_data(workout_data):
    exercise_names = []
    if not isinstance(workout_data, dict):
        return exercise_names
    for set_key in workout_data:
        for exercise_name in workout_data.get(set_key, []):
            if exercise_name not in exercise_names:
                exercise_names.append(exercise_name)
    return exercise_names


def _ensure_assistant_conversation(user_id):
    convo_id = session.get('assistant_conversation_id')
    if convo_id:
        return convo_id
    latest_df = get_latest_assistant_conversation(user_id)
    if latest_df is not None and not latest_df.empty:
        convo_id = latest_df['id'].iloc[0]
        session['assistant_conversation_id'] = convo_id
        return convo_id
    convo_id = create_assistant_conversation(user_id, title='New chat')
    migrate_assistant_messages_to_conversation(user_id, convo_id)
    session['assistant_conversation_id'] = convo_id
    return convo_id


def _get_workout_type_id(workout_type_name):
    if not workout_type_name:
        return None
    workout_types_df = get_workout_types()
    for _, row in workout_types_df.iterrows():
        if str(row['name']).lower() == str(workout_type_name).lower():
            return str(row['id'])
    return None


def _normalize_action(action):
    if not isinstance(action, dict):
        return None
    action_type = action.get('type')
    if action_type == 'create_workout':
        name = (action.get('name') or 'New Workout').strip()
        workout_type = (action.get('workout_type') or '').strip()
        description = (action.get('description') or '').strip()
        sets = action.get('sets') or []
        exercises = action.get('exercises') or []
        if exercises and not sets:
            sets = [{'name': 'Set 1', 'exercises': exercises}]
        return {
            'type': 'create_workout',
            'name': name,
            'workout_type': workout_type,
            'description': description,
            'sets': sets
        }
    if action_type == 'log_workout':
        workout_name = (action.get('workout_name') or '').strip()
        if not workout_name:
            return None
        return {
            'type': 'log_workout',
            'workout_name': workout_name,
            'completed_at': (action.get('completed_at') or '').strip(),
            'feedback': (action.get('feedback') or '').strip()
        }
    if action_type == 'edit_workout':
        name = (action.get('workout_name') or action.get('name') or '').strip()
        if not name:
            return None
        new_name = (action.get('new_name') or '').strip()
        description = (action.get('description') or '').strip()
        sets = action.get('sets') or []
        exercises = action.get('exercises') or []
        if exercises and not sets:
            sets = [{'name': 'Set 1', 'exercises': exercises}]
        return {
            'type': 'edit_workout',
            'workout_name': name,
            'new_name': new_name,
            'description': description,
            'sets': sets
        }
    if action_type == 'delete_workout':
        workout_name = (action.get('workout_name')
                        or action.get('name') or '').strip()
        workout_id = (action.get('workout_id')
                      or action.get('id') or '').strip()
        if not workout_name and not workout_id:
            return None
        return {
            'type': 'delete_workout',
            'workout_name': workout_name,
            'workout_id': workout_id
        }
    return None


def _summarize_action(action):
    if action['type'] == 'create_workout':
        sets = action.get('sets') or []
        return {
            'title': 'Create workout',
            'summary': f"{action.get('name')} · {action.get('workout_type') or 'type needed'} · {len(sets)} set(s)"
        }
    if action['type'] == 'log_workout':
        return {
            'title': 'Log workout',
            'summary': f"{action.get('workout_name') or 'workout needed'} · {action.get('completed_at') or 'now'}"
        }
    if action['type'] == 'edit_workout':
        return {
            'title': 'Edit workout',
            'summary': f"{action.get('workout_name') or 'workout needed'} · update"
        }
    if action['type'] == 'delete_workout':
        return {
            'title': 'Delete workout',
            'summary': action.get('workout_name') or action.get('workout_id') or 'workout needed'
        }
    return {
        'title': 'Action',
        'summary': ''
    }


def _apply_action(action, user_id):
    if action['type'] == 'create_workout':
        workout_type_id = _get_workout_type_id(action.get('workout_type'))
        if not workout_type_id:
            return {'status': 'error', 'message': 'Workout type not found.'}
        workout_data = {}
        for idx, set_obj in enumerate(action.get('sets') or [], start=1):
            if not isinstance(set_obj, dict):
                continue
            set_name = (set_obj.get('name') or f"Set {idx}").strip()
            exercises = [str(item).strip() for item in (
                set_obj.get('exercises') or []) if str(item).strip()]
            if exercises:
                workout_data[set_name] = exercises
        if not workout_data:
            return {'status': 'error', 'message': 'No exercises provided for workout.'}
        workout_id = create_workout(
            action.get('name'),
            workout_type_id,
            action.get('description') or '',
            json.dumps(workout_data),
            user_id=user_id
        )
        return {'status': 'success', 'message': f"Created workout '{action.get('name')}'.", 'workout_id': workout_id}

    if action['type'] == 'log_workout':
        workout_name = action.get('workout_name')
        if not workout_name:
            return {'status': 'error', 'message': 'Workout name is required to log.'}
        workouts_df = get_workouts(user_id=user_id)
        workout_match = workouts_df[workouts_df['name'].str.lower(
        ) == workout_name.lower()]
        if workout_match.empty:
            return {'status': 'error', 'message': f"Workout '{workout_name}' not found."}
        workout_id = workout_match['id'].iloc[0]
        feedback = action.get('feedback') or ''
        completed_at = action.get('completed_at') or ''
        if completed_at:
            try:
                datetime.strptime(completed_at, "%Y-%m-%dT%H:%M")
            except ValueError:
                return {'status': 'error', 'message': 'completed_at must be YYYY-MM-DDTHH:MM.'}
        create_workout_log(workout_id, user_id, feedback,
                           past_date=completed_at)
        return {'status': 'success', 'message': f"Logged workout '{workout_name}'."}

    if action['type'] == 'edit_workout':
        workout_name = action.get('workout_name')
        if not workout_name:
            return {'status': 'error', 'message': 'Workout name is required to edit.'}
        workouts_df = get_workouts(user_id=user_id)
        workout_match = workouts_df[workouts_df['name'].str.lower(
        ) == workout_name.lower()]
        if workout_match.empty:
            return {'status': 'error', 'message': f"Workout '{workout_name}' not found."}
        workout_id = workout_match['id'].iloc[0]

        updates = []
        sets = action.get('sets') or []
        if sets:
            workout_data = {}
            for idx, set_obj in enumerate(sets, start=1):
                if not isinstance(set_obj, dict):
                    continue
                set_name = (set_obj.get('name') or f"Set {idx}").strip()
                exercises = [str(item).strip() for item in (
                    set_obj.get('exercises') or []) if str(item).strip()]
                if exercises:
                    workout_data[set_name] = exercises
            if workout_data:
                update_workout_data(workout_id, json.dumps(workout_data))
                updates.append('exercises')

        new_name = action.get('new_name') or ''
        description = action.get('description') or ''
        if new_name or description:
            current_name = workout_match['name'].iloc[0]
            current_desc = workout_match['description'].iloc[0] if 'description' in workout_match.columns else ''
            update_workout_meta(
                workout_id,
                new_name if new_name else current_name,
                description if description else current_desc
            )
            updates.append('details')

        if not updates:
            return {'status': 'error', 'message': 'No changes provided for workout.'}
        return {'status': 'success', 'message': f"Updated workout '{workout_name}'."}

    if action['type'] == 'delete_workout':
        workout_id = action.get('workout_id') or ''
        workout_name = action.get('workout_name') or ''
        workouts_df = get_workouts(user_id=user_id)
        if workouts_df.empty:
            return {'status': 'error', 'message': 'No workouts available to delete.'}
        if workout_id:
            workout_match = workouts_df[workouts_df['id'] == workout_id]
        else:
            workout_match = workouts_df[workouts_df['name'].str.lower(
            ) == workout_name.lower()]
        if workout_match.empty:
            return {'status': 'error', 'message': f"Workout '{workout_name or workout_id}' not found."}
        target_id = workout_match['id'].iloc[0]
        delete_workout_item(target_id)
        target_name = workout_match['name'].iloc[0]
        return {'status': 'success', 'message': f"Deleted workout '{target_name}'."}

    return {'status': 'error', 'message': 'Unsupported action.'}


@main.route('/assistant/history', methods=['GET'])
@auth_required
def assistant_history():
    user_id = session['user_id']
    convo_id = _ensure_assistant_conversation(user_id)
    history_df = get_assistant_messages_by_conversation(
        user_id, convo_id, limit=100)
    if history_df.empty:
        return {'mode': session.get('assistant_mode', 'approval'), 'messages': [], 'conversation_id': convo_id}
    history_df = history_df.sort_values('created_at')
    messages = []
    for _, row in history_df.iterrows():
        actions_raw = row.get('actions_json')
        results_raw = row.get('action_results_json')
        actions = json.loads(actions_raw) if actions_raw and str(
            actions_raw) != 'nan' else []
        action_results = json.loads(results_raw) if results_raw and str(
            results_raw) != 'nan' else []
        messages.append({
            'id': row['id'],
            'conversation_id': row.get('conversation_id'),
            'role': row['role'],
            'content': row['content'],
            'mode': row.get('mode'),
            'actions': actions,
            'action_results': action_results,
            'created_at': row['created_at']
        })
    return {'mode': session.get('assistant_mode', 'approval'), 'messages': messages, 'conversation_id': convo_id}


@main.route('/assistant/conversations', methods=['GET'])
@auth_required
def assistant_conversations():
    user_id = session['user_id']
    convo_id = _ensure_assistant_conversation(user_id)
    convos_df = get_assistant_conversations(user_id)
    conversations = []
    if convos_df is not None and not convos_df.empty:
        convos_df = convos_df.sort_values('updated_at', ascending=False)
        for _, row in convos_df.iterrows():
            conversations.append({
                'id': row['id'],
                'title': row['title'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at']
            })
    return {'current_id': convo_id, 'conversations': conversations}


@main.route('/assistant/conversations/new', methods=['POST'])
@auth_required
def assistant_conversations_new():
    user_id = session['user_id']
    convo_id = create_assistant_conversation(user_id, title='New chat')
    session['assistant_conversation_id'] = convo_id
    return {'status': 'ok', 'conversation_id': convo_id}


@main.route('/assistant/conversations/select', methods=['POST'])
@auth_required
def assistant_conversations_select():
    payload = request.get_json(silent=True) or {}
    convo_id = payload.get('conversation_id')
    if not convo_id:
        return {'error': 'Conversation required.'}, 400
    user_id = session['user_id']
    convos_df = get_assistant_conversations(user_id)
    if convos_df.empty or convo_id not in convos_df['id'].values:
        return {'error': 'Conversation not found.'}, 404
    session['assistant_conversation_id'] = convo_id
    return {'status': 'ok', 'conversation_id': convo_id}


@main.route('/assistant/conversations/rename', methods=['POST'])
@auth_required
def assistant_conversations_rename():
    payload = request.get_json(silent=True) or {}
    convo_id = payload.get('conversation_id')
    title = (payload.get('title') or '').strip()
    if not convo_id or not title:
        return {'error': 'Conversation and title required.'}, 400
    user_id = session['user_id']
    convos_df = get_assistant_conversations(user_id)
    if convos_df.empty or convo_id not in convos_df['id'].values:
        return {'error': 'Conversation not found.'}, 404
    update_assistant_conversation_title(convo_id, title[:80])
    return {'status': 'ok'}


@main.route('/assistant/mode', methods=['POST'])
@auth_required
def assistant_mode():
    payload = request.get_json(silent=True) or {}
    mode = (payload.get('mode') or 'approval').strip().lower()
    if mode not in ['approval', 'auto']:
        return {'error': 'Invalid mode.'}, 400
    user_id = session['user_id']
    update_user_preferences_mode(user_id, mode)
    session['assistant_mode'] = mode
    return {'status': 'ok', 'mode': mode}


@main.route('/assistant/actions/confirm', methods=['POST'])
@auth_required
def assistant_actions_confirm():
    payload = request.get_json(silent=True) or {}
    message_id = payload.get('message_id')
    action_index = payload.get('action_index')
    if message_id is None or action_index is None:
        return {'error': 'Missing action reference.'}, 400
    try:
        action_index = int(action_index)
    except (TypeError, ValueError):
        return {'error': 'Invalid action index.'}, 400
    user_id = session['user_id']
    history_df = get_assistant_messages(user_id, limit=200)
    msg_row = history_df[history_df['id'] == message_id]
    if msg_row.empty:
        return {'error': 'Action not found.'}, 404
    actions_raw = msg_row['actions_json'].iloc[0]
    actions = json.loads(actions_raw) if actions_raw and str(
        actions_raw) != 'nan' else []
    if action_index >= len(actions):
        return {'error': 'Action index out of range.'}, 400
    action = actions[action_index]
    result = _apply_action(action, user_id)
    remaining_actions = [a for idx, a in enumerate(
        actions) if idx != action_index]
    existing_results_raw = msg_row['action_results_json'].iloc[0]
    existing_results = json.loads(existing_results_raw) if existing_results_raw and str(
        existing_results_raw) != 'nan' else []
    existing_results.append(result)
    update_assistant_message_actions(
        message_id,
        json.dumps(remaining_actions) if remaining_actions else None,
        json.dumps(existing_results) if existing_results else None
    )
    create_assistant_message(
        user_id=user_id,
        role='assistant',
        content=result.get('message', 'Action applied.'),
        mode=session.get('assistant_mode', 'approval'),
        actions_json=None,
        action_results_json=json.dumps([result]),
        conversation_id=msg_row['conversation_id'].iloc[0] if 'conversation_id' in msg_row.columns else None
    )
    return {'message': result.get('message', 'Action applied.'), 'result': result}


@main.route('/assistant/actions/dismiss', methods=['POST'])
@auth_required
def assistant_actions_dismiss():
    payload = request.get_json(silent=True) or {}
    message_id = payload.get('message_id')
    action_index = payload.get('action_index')
    if message_id is None or action_index is None:
        return {'error': 'Missing action reference.'}, 400
    try:
        action_index = int(action_index)
    except (TypeError, ValueError):
        return {'error': 'Invalid action index.'}, 400
    user_id = session['user_id']
    history_df = get_assistant_messages(user_id, limit=200)
    msg_row = history_df[history_df['id'] == message_id]
    if msg_row.empty:
        return {'error': 'Action not found.'}, 404
    actions_raw = msg_row['actions_json'].iloc[0]
    actions = json.loads(actions_raw) if actions_raw and str(
        actions_raw) != 'nan' else []
    if action_index >= len(actions):
        return {'error': 'Action index out of range.'}, 400
    remaining_actions = [a for idx, a in enumerate(
        actions) if idx != action_index]
    update_assistant_message_actions(
        message_id,
        json.dumps(remaining_actions) if remaining_actions else None,
        msg_row['action_results_json'].iloc[0]
    )
    return {'status': 'ok'}


@main.route('/assistant/message', methods=['POST'])
@auth_required
def assistant_message():
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get('message') or '').strip()
    mode = (payload.get('mode') or session.get(
        'assistant_mode') or 'approval').strip().lower()
    if not user_message:
        return {'error': 'Message required.'}, 400

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return {'error': 'OpenAI API key is not configured.'}, 500

    user_id = session['user_id']
    convo_id = _ensure_assistant_conversation(user_id)
    create_assistant_message(user_id=user_id, role='user',
                             content=user_message, mode=mode, conversation_id=convo_id)
    if len(user_message) >= 3:
        convo_df = get_assistant_conversation(user_id, convo_id)
        if convo_df is None or convo_df.empty or (convo_df['title'].iloc[0] or '').strip().lower() in ['new chat', '']:
            update_assistant_conversation_title(convo_id, user_message[:60])
    touch_assistant_conversation(convo_id)

    history_df = get_assistant_messages_by_conversation(
        user_id, convo_id, limit=12)
    history_df = history_df.sort_values('created_at')
    history_messages = []
    for _, row in history_df.iterrows():
        if not row['content']:
            continue
        history_messages.append(
            {'role': row['role'], 'content': row['content']})

    context = _build_assistant_context(user_id)

    system_prompt = (
        "You are BodyGuru's AI assistant. You can help create, edit, delete workouts, log workouts, and answer questions about workouts, logs, and exercises. "
        "Only use the data provided in CONTEXT. If information is missing, ask a follow-up question. "
        f"Execution mode: {mode}. If mode is approval, explain what you will do and ask for confirmation before proceeding. "
        "Keep responses concise and practical."
    )

    client = OpenAI(api_key=api_key)

    def get_assistant_text(messages):
        if hasattr(client, 'responses'):
            response = client.responses.create(
                model='gpt-5-mini',
                input=messages
            )
            response_text = getattr(response, 'output_text', '') or ''
            if not response_text and hasattr(response, 'output'):
                for item in response.output:
                    if getattr(item, 'content', None):
                        for part in item.content:
                            if getattr(part, 'text', None):
                                response_text += part.text
            return response_text

        response = client.chat.completions.create(
            model='gpt-5-mini',
            messages=messages
        )
        return response.choices[0].message.content or ''

    response_text = ''
    try:
        response_text = get_assistant_text([
            {'role': 'system', 'content': system_prompt},
            {'role': 'system', 'content': f"CONTEXT: {json.dumps(context)}"},
            *history_messages
        ])
    except Exception as e:
        return {'error': f'OpenAI error: {str(e)}'}, 500

    action_prompt = (
        "Return JSON only with the schema: {\"actions\": [ ... ]}. "
        "Valid action types: create_workout, log_workout, edit_workout, delete_workout. "
        "create_workout fields: name, workout_type, description, sets (list of {name, exercises}) or exercises. "
        "log_workout fields: workout_name, completed_at (YYYY-MM-DDTHH:MM optional), feedback. "
        "edit_workout fields: workout_name, new_name, description, sets (list of {name, exercises}) or exercises. "
        "delete_workout fields: workout_name or workout_id. "
        "If a required field is missing, return {\"actions\": []}."
    )

    actions = []
    try:
        should_run_actions = bool(re.search(
            r"\b(create|log|edit|update|rename|change|delete|remove)\b.*\bworkout\b", user_message, re.IGNORECASE))
        if should_run_actions:
            action_text = get_assistant_text([
                {'role': 'system', 'content': action_prompt},
                {'role': 'system',
                    'content': f"CONTEXT: {json.dumps(context)}"},
                {'role': 'user', 'content': user_message},
                {'role': 'assistant', 'content': response_text}
            ])
        else:
            action_text = ''
        action_obj = json.loads(action_text) if action_text else {
            'actions': []}
        raw_actions = action_obj.get(
            'actions', []) if isinstance(action_obj, dict) else []
        for raw in raw_actions:
            normalized = _normalize_action(raw)
            if normalized:
                summary = _summarize_action(normalized)
                normalized.update(summary)
                actions.append(normalized)
    except Exception:
        actions = []

    action_results = []
    if mode == 'auto' and actions:
        for action in actions:
            action_results.append(_apply_action(action, user_id))

    assistant_message_id = create_assistant_message(
        user_id=user_id,
        role='assistant',
        content=response_text,
        mode=mode,
        actions_json=json.dumps(actions) if actions else None,
        action_results_json=json.dumps(
            action_results) if action_results else None,
        conversation_id=convo_id
    )

    def event_stream():
        chunk_size = 60
        for idx in range(0, len(response_text), chunk_size):
            chunk = response_text[idx:idx + chunk_size]
            yield f"data: {json.dumps({'type': 'delta', 'content': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'actions', 'message_id': assistant_message_id, 'actions': actions, 'action_results': action_results})}\n\n"

    return Response(stream_with_context(event_stream()), mimetype='text/event-stream')
