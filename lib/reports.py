from lib.queries import q_create_user_report, q_get_user_reports, q_update_user_reports
from extensions import DB, create_connection
import pandas as pd
import os
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from datetime import datetime
import json
import matplotlib
import pathlib
matplotlib.use('Agg')

BASE_URL = os.getenv('BASE_URL')
target_directory = ''.join((BASE_URL, '/static/user_reports'))
print(BASE_URL, target_directory)


def transform_log_data(logs):
    log_exercise_data = pd.DataFrame(
        columns=['workout', 'workout_date', 'exercise', 'reps', 'weight', 'feel'])
    i = 0
    for index, log in logs.iterrows():
        feedback_data = json.loads(log['feedback_data'])
        exercises = feedback_data.keys()
        for exercise in exercises:
            obj = feedback_data[exercise]
            log_exercise_data.loc[i, 'workout'] = log['workout_name']
            log_exercise_data.loc[i, 'workout_date'] = log['completed_at']
            log_exercise_data.loc[i, 'exercise'] = exercise
            log_exercise_data.loc[i, 'reps'] = obj['reps']
            log_exercise_data.loc[i, 'weight'] = obj['weight']
            log_exercise_data.loc[i, 'feel'] = obj['feel']
            i += 1
    sorted_log_data = log_exercise_data.sort_values(by=['workout_date'])
    return sorted_log_data


def generate_volume_report(log_exercise_data):
    log_exercise_data['volume'] = log_exercise_data['reps'].astype(int) * \
        log_exercise_data['weight'].astype(int)
    total_workout_volume = log_exercise_data.groupby(
        ['workout', 'workout_date'], as_index=False)['volume'].sum()

    return total_workout_volume


def generate_progress_report(log_exercise_data):
    exercise_progress = {}
    for exercise in log_exercise_data['exercise']:
        df = log_exercise_data[log_exercise_data['exercise'] == exercise]
        df['volume'] = df['reps'].astype(int) * df['weight'].astype(int)
        exercise_data = df[['workout_date', 'reps',
                            'weight', 'feel', 'volume']].to_dict(orient='records')
        exercise_progress[exercise] = exercise_data
    return exercise_progress


def plot_exercise(exercise_name, records, user_id):
    dates = [datetime.strptime(
        d['workout_date'], '%Y-%m-%d %H:%M:%S.%f') for d in records]
    reps = [int(d['reps']) for d in records]
    weights = [int(d['weight']) for d in records]
    volume = [int(d['volume']) for d in records]

    plt.figure(figsize=(10, 4))

    date_range = (max(dates) - min(dates)).days
    if date_range > 120:
        plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    elif date_range > 20:
        plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())
    else:
        plt.gca().xaxis.set_major_locator(mdates.DayLocator())

    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

    plt.plot(dates, reps, label='Reps')
    plt.plot(dates, weights, label='Weight')
    plt.plot(dates, volume, label='Volume')

    plt.scatter(dates, reps, marker='o')
    plt.scatter(dates, weights,
                marker='o')
    plt.scatter(dates, volume,
                marker='o')

    plt.gcf().autofmt_xdate()
    plt.title(exercise_name.replace('_', ' '))
    plt.xlabel('Date')
    plt.ylabel('Reps/Weight')
    plt.legend()

    # Save plot to file
    plot_filename = f'{exercise_name.replace(" ", "_")}_{user_id}_plot.png'
    target_path = os.path.join(target_directory, plot_filename)
    plt.savefig(target_path)
    plt.close()
    return plot_filename


def create_report_record(user_id, report_name, filename):
    conn = create_connection(DB)
    cur = conn.cursor()
    created_at = datetime.now()
    cur.execute(q_create_user_report, (user_id, created_at,
                created_at, report_name, filename))
    conn.commit()


def update_report_record(user_id, report_name, filename):
    conn = create_connection(DB)
    cur = conn.cursor()
    updated_at = datetime.now()
    q_update_user_reports_formatted = q_update_user_reports.format(
        report_name=report_name, filename=filename, updated_at=updated_at, user_id=user_id)
    cur.execute(q_update_user_reports_formatted)
    conn.commit()


def create_progress_plot(progress_report, user_id):
    files = {}
    for exercise, records in progress_report.items():
        plot_filename = plot_exercise(exercise, records, user_id)
        files[exercise] = plot_filename
    return files


def get_reports(user_id):
    conn = create_connection(DB)
    q_get_user_reports_formatted = q_get_user_reports.format(user_id=user_id)
    reports = pd.read_sql_query(q_get_user_reports_formatted, conn)
    return reports


def run_report_flow(logs, user_id):
    reports = get_reports(user_id)
    user_has_reports = len(reports.index) > 0
    if user_has_reports:
        last_report_updated = pd.to_datetime(reports['updated_at']).max()
        last_log_created = pd.to_datetime(logs['created_at']).max()
    else:
        last_report_updated = 0
        last_log_created = 1

    if last_report_updated >= last_log_created:
        files = [row for row in reports['filename']]
    else:
        log_exercise_data = transform_log_data(logs)
        progress_report = generate_progress_report(log_exercise_data)
        file_dict = create_progress_plot(progress_report, user_id)
        files = []
        for exercise in file_dict.keys():
            report_name = 'progress_report_' + exercise
            filename = file_dict[exercise]
            files.append(filename)
            if user_has_reports & (report_name in reports['report_name'].unique()):
                update_report_record(user_id, report_name, filename)
            else:
                create_report_record(user_id, report_name, filename)
    return files
