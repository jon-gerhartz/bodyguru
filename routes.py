from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app, abort
from exp.landing import landing_data
import json
from lib.crud import *
from lib.data_meta import *
from lib.reports import run_report_flow
from utils.app_functions import auth_required
import os
from werkzeug.utils import secure_filename
from utils.storage import get_storage_config, get_s3_client, get_bucket_name, presign_get_url

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
        cleaned = [str(item).strip() for item in exercises if str(item).strip()]
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
    workout = get_workout(workout_id)
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
    workout = get_workout(workout_id)
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
    workout = get_workout(workout_id)
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
