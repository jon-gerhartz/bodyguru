db_exists = """
SELECT 1 FROM pg_database WHERE datname = 'workout';
"""

create_db = """
CREATE DATABASE workout;
"""

# add_uuid_extension = """
# CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
# """

# DDL for reference tables
init_exercise_types = """
CREATE TABLE IF NOT EXISTS exercise_types (
	id TEXT PRIMARY KEY,
    name TEXT UNIQUE
);
"""

init_muscle_group_name = """
CREATE TABLE IF NOT EXISTS muscle_group_names (
	id TEXT PRIMARY KEY,
    name TEXT UNIQUE
);
"""

init_exercise_equipment = """
CREATE TABLE IF NOT EXISTS exercise_equipment (
	id TEXT PRIMARY KEY,
    name TEXT UNIQUE
);
"""

init_workout_type = """
CREATE TABLE IF NOT EXISTS workout_types (
	id TEXT PRIMARY KEY,
    name TEXT UNIQUE
);
"""

init_user_status = """
CREATE TABLE IF NOT EXISTS user_status (
	id TEXT PRIMARY KEY,
    name TEXT UNIQUE
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

init_users = """
CREATE TABLE IF NOT EXISTS users (
	id TEXT PRIMARY KEY, -- UUIDs as text
	email TEXT UNIQUE,
	password_hash bytea, -- bytea equivalent in SQLite is BLOB
	created_at TEXT -- SQLite does not support 'with time zone'
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

# alter statements for core tables
add_link_to_exercises = """
ALTER TABLE exercises ADD COLUMN IF NOT EXISTS link TEXT;
"""

add_name_to_users = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS name TEXT;
"""

add_status_to_users = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS status_id TEXT DEFAULT 1;
"""

add_status_foreign_key = """
ALTER TABLE users ADD FOREIGN KEY (status_id) REFERENCES user_status(id) ON DELETE SET NULL;
"""

# DDL for user tables

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
    (4, 'bodyweight')
ON CONFLICT (name)
DO NOTHING;
"""

insert_exercise_equipment = """
INSERT INTO exercise_equipment (id, name)
VALUES
	(1, 'dumbbell'),
    (2, 'barbell'),
    (3, 'kettlebell'),
    (4, 'bodyweight'),
    (5, 'jump rope'),
    (6, 'cable'),
    (7, 'other'),
    (8, 'machine'),
    (9, 'e-z curl bar'),
    (10, 'bands'),
    (11, 'medicine ball'),
    (12, 'exercise ball'),
    (13, 'bench')
ON CONFLICT (name)
DO NOTHING;
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
    (10, 'back'),
    (11, 'lats'),
    (12, 'middle back'),
    (13, 'lower back'),
    (14, 'glutes'),
    (15, 'neck'),
    (16, 'traps'),
    (17, 'abductors'),
    (18, 'adductors'),
    (19, 'forearms')
ON CONFLICT (name)
DO NOTHING;
"""

insert_workout_types = """
INSERT INTO workout_types (id, name)
VALUES
	(1, 'lifting'),
    (2, 'cardio'),
    (3, 'hiit'),
    (4, 'functional')
ON CONFLICT (name)
DO NOTHING;
"""

insert_user_status = """
INSERT INTO user_status (id, name)
VALUES
	(1, 'pending'),
    (2, 'active'),
    (3, 'closed')
ON CONFLICT (name)
DO NOTHING;
"""

# DDL for password reset tbl
init_password_reset_request = """
CREATE TABLE IF NOT EXISTS password_reset_request (
    user_id TEXT,
    url_var TEXT,
    created_at TEXT
);
"""
