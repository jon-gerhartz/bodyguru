# DDL for reference tables
init_exercise_types = """
CREATE TABLE IF NOT EXISTS exercise_types (
	id TEXT PRIMARY KEY,
    name TEXT
);
"""

init_muscle_group_name = """
CREATE TABLE IF NOT EXISTS muscle_group_names (
	id TEXT PRIMARY KEY,
    name TEXT
);
"""

init_exercise_equipment = """
CREATE TABLE IF NOT EXISTS exercise_equipment (
	id TEXT PRIMARY KEY,
    name TEXT
);
"""

init_workout_type = """
CREATE TABLE IF NOT EXISTS workout_types (
	id TEXT PRIMARY KEY,
    name TEXT
);
"""

# DDL for core tables
init_exercises = """
CREATE TABLE IF NOT EXISTS exercises (
	id TEXT PRIMARY KEY, -- UUIDs as text
	name TEXT NOT NULL,
    exercise_type_id TEXT,
    exercise_equipment_id TEXT,
	description TEXT,
    muscle_group_id TEXT,
    deleted INTEGER DEFAULT 0,
    FOREIGN KEY(exercise_type_id) REFERENCES exercise_types(id) ON DELETE SET NULL,
    FOREIGN KEY(exercise_equipment_id) REFERENCES exercise_equipment(id) ON DELETE SET NULL,
    FOREIGN KEY(muscle_group_id) REFERENCES muscle_group_names(id) ON DELETE SET NULL
);
"""

init_workouts = """
CREATE TABLE IF NOT EXISTS workouts (
	id TEXT PRIMARY KEY, -- UUIDs as text
	name TEXT NOT NULL,
	workout_type_id TEXT,
	description TEXT,
	workout_data TEXT, -- JSON data as text
    deleted INTEGER DEFAULT 0,
    FOREIGN KEY(workout_type_id) REFERENCES workout_types(id) ON DELETE SET NULL
);
"""

init_workout_logs = """
CREATE TABLE IF NOT EXISTS workout_logs (
	id TEXT PRIMARY KEY, -- UUIDs as text
	workout_id TEXT, -- UUIDs as text
	user_id TEXT, -- UUIDs as text
	feedback_data TEXT, -- JSON data as text
    completed_at TEXT,
	created_at TEXT, -- SQLite does not support 'with time zone'
    deleted INTEGER DEFAULT 0,
	FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE SET NULL,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
"""

# DDL for user tables
init_users = """
CREATE TABLE IF NOT EXISTS users (
	id TEXT PRIMARY KEY, -- UUIDs as text
	email TEXT UNIQUE,
	password_hash BLOB, -- bytea equivalent in SQLite is BLOB
	created_at TEXT -- SQLite does not support 'with time zone'
);
"""

init_user_workouts = """
CREATE TABLE IF NOT EXISTS user_workouts (
	user_id TEXT, -- UUIDs as text
	workout_id TEXT, -- UUIDs as text
	FOREIGN KEY(workout_id) REFERENCES workouts(id) ON DELETE SET NULL,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
"""

init_user_exercises = """
CREATE TABLE IF NOT EXISTS user_exercises (
	user_id TEXT, -- UUIDs as text
	exercise_id TEXT, -- UUIDs as text
	FOREIGN KEY(exercise_id) REFERENCES exercises(id) ON DELETE SET NULL,
	FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
"""

init_user_reports = """
CREATE TABLE IF NOT EXISTS user_reports (
    user_id TEXT,
    created_at TEXT,
    updated_at TEXT,
    report_name TEXT,
    filename TEXT
);
"""

# DDL for reference table data insertion
insert_exercise_types = """
INSERT INTO exercise_types (id, name)
VALUES
	(1, 'lift'),
    (2, 'functional'),
    (3, 'cardio'),
    (4, 'bodyweight');
"""

insert_exercise_equipment = """
INSERT INTO exercise_equipment (id, name)
VALUES
	(1, 'dumbbell'),
    (2, 'barbell'),
    (3, 'kettlebell'),
    (4, 'bodyweight'),
    (5, 'jump rope'),
    (6, 'cable');
"""

insert_muscle_group_names = """
INSERT INTO muscle_group_names (id, name)
VALUES
	(1, 'quadriceps'),
    (2, 'hamstrings'),
    (3, 'calves'),
    (4, 'chest'),
    (5, 'triceps'),
    (6, 'biceps'),
    (7, 'shoulders'),
    (8, 'abs'),
    (9, 'neck'),
    (10, 'back');
"""

insert_workout_types = """
INSERT INTO workout_types (id, name)
VALUES
	(1, 'lifting'),
    (2, 'cardio'),
    (3, 'hiit'),
    (4, 'functional');
"""
# full run list
run_list = [init_exercise_types, init_muscle_group_name, init_exercise_equipment, init_workout_type, init_exercises, init_workouts, init_workout_logs,
            init_users, init_user_workouts, init_user_exercises, init_user_reports]


insert_run_list = [insert_exercise_types, insert_exercise_equipment,
                   insert_muscle_group_names, insert_workout_types]


def run_migrations(conn):
    try:
        cursor = conn.cursor()
        for i in run_list:
            cursor.execute(i)
        conn.commit()
        message = 'successfully commited migrations'
    except Exception as e:
        message = e
    return message
