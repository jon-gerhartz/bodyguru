from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import json
from lib.crud import *
from lib.data_meta import *
from lib.reports import run_report_flow
import pandas as pd
from utils.app_functions import auth_required

main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def index():
    if 'authenticated' not in session.keys():
        session['authenticated'] = False

    if session['authenticated'] == True:
        return redirect(url_for('main.dashboard', user_id=session['user_id']))
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
    exercises = get_exercises(user_id)
    exercises_list = exercises.to_dict(orient='records')
    exercises_dict = {'name': 'exercise', 'data': exercises_list}
    return exercises_dict


@main.route('/exercise-details/<exercise_id>', methods=['GET', 'POST'])
@auth_required
def details(exercise_id):
    exercise = get_exercise(exercise_id)
    return render_template('exercise_details.html', exercise=exercise)


@main.route('/delete-exercise/<exercise_id>', methods=['POST'])
@auth_required
def delete_exercise(exercise_id):
    resp = delete_exercise_item(exercise_id)
    return redirect(url_for('main.library'))


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
    workout_types = get_workout_types()
    workout_types_list = workout_types.to_dict(orient='records')
    workout_types_dict = {'name': 'workout type', 'data': workout_types_list}
    return workout_types_dict


@main.route('/workouts', methods=['GET', 'POST'])
@auth_required
def workouts():
    user_id = session['user_id']
    if request.method == 'GET':
        workouts = get_workouts(user_id=user_id)
        col_data = create_filer_col_dict(workout_filter_cols, workouts)
        return render_template('workouts.html', workouts=workouts, data_cols=workout_filter_cols, col_data=col_data)
    else:
        name = request.form.get('name')
        w_type = request.form.get('type')
        description = request.form.get('description')
        workout_data = request.form.get('workout_data')
        create_workout(name, w_type, description,
                       workout_data, user_id=user_id)
        return redirect(url_for('main.workouts'))


@main.route('/workout-details/<workout_id>', methods=['GET', 'POST'])
@auth_required
def workout_details(workout_id):
    workout = get_workout(workout_id)
    workout_data_str = workout['workout_data'][0]
    workout_data = json.loads(workout_data_str)
    return render_template('workout_details.html', workout=workout, workout_data=workout_data)


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
        logs = get_workout_logs(user_id)
        col_data = create_filer_col_dict(log_filter_cols, logs)
        return render_template('log.html', logs=logs, data_cols=log_filter_cols, col_data=col_data)
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
