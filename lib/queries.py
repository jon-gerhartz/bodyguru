# queries for exercises
q_get_exercises_all = """
SELECT 
	a.id
	,a.name
	,b.name as type
	,c.name as equipment
	,a.description
	,d.name as muscle_group_name
FROM exercises a
JOIN exercise_types b on b.id = a.exercise_type_id
JOIN exercise_equipment c on c.id = a.exercise_equipment_id
JOIN muscle_group_names d on d.id = a.muscle_group_id
LEFT JOIN user_exercises f on f.exercise_id = a.id
WHERE (f.user_id = '{user_id}' OR f.user_id is null) and deleted = 0;
"""

# queries for exercises
q_get_exercises_fp_users = """
SELECT 
	a.id
	,a.name
	,b.name as type
	,c.name as equipment
	,a.description
	,d.name as muscle_group_name
FROM exercises a
JOIN exercise_types b on b.id = a.exercise_type_id
JOIN exercise_equipment c on c.id = a.exercise_equipment_id
JOIN muscle_group_names d on d.id = a.muscle_group_id
LEFT JOIN user_exercises f on f.exercise_id = a.id
WHERE (f.user_id = '{user_id}' OR b.id = 5::text) and deleted = 0;
"""

q_get_exercise = """
SELECT *
FROM (
	SELECT 
		a.id
		,a.name
		,b.name as type
		,c.name as equipment
		,a.description
		,d.name as muscle_group_name
        ,f.user_id is null as is_default_exercise
        ,a.link
        ,a.video_slug
	FROM exercises a
	JOIN exercise_types b on b.id = a.exercise_type_id
	JOIN exercise_equipment c on c.id = a.exercise_type_id
	JOIN muscle_group_names d on d.id = a.muscle_group_id
    LEFT JOIN user_exercises f on f.exercise_id = a.id) aa
WHERE {lookup_col} = '{lookup_val}'
"""

q_create_exercise = """
INSERT INTO exercises (id, name, exercise_type_id, exercise_equipment_id, description, muscle_group_id)
VALUES (:id, :name, :exercise_type_id, :exercise_equipment_id, :description, :muscle_group_id)
"""

q_delete_exercise = """
UPDATE exercises
SET deleted = 1
WHERE id = '{exercise_id}'
"""

q_update_exercise_details = """
UPDATE exercises
   SET description = :description
 WHERE id = :id
"""

q_update_exercise_video = """
UPDATE exercises
   SET video_slug = :video_slug
 WHERE id = :id
"""

q_get_exercises_admin = """
SELECT
    a.id
    ,a.name
    ,a.exercise_type_id
    ,b.name as type
    ,a.description
    ,a.video_slug
FROM exercises a
JOIN exercise_types b on b.id = a.exercise_type_id
WHERE a.deleted = 0
ORDER BY name;
"""

# queries for workouts
q_get_workouts_all = """
SELECT 
	a.id
	,a.name
	,b.name as type
	,a.description
	,a.workout_data
    ,c.user_id is null as is_default_workout
    ,u.name as shared_from_name
FROM workouts a
JOIN workout_types b on b.id = a.workout_type_id
LEFT JOIN user_workouts c on c.workout_id = a.id
LEFT JOIN workout_shares ws on ws.accepted_workout_id = a.id and ws.receiver_user_id = '{user_id}' and ws.status = 'accepted'
LEFT JOIN users u on u.id = ws.sender_user_id
WHERE (c.user_id = '{user_id}' or c.user_id is null) and deleted = 0;
"""

q_get_workout = """
SELECT *
FROM (
	SELECT 
		a.id
		,a.name
		,b.name as type
		,a.description
		,a.workout_data
        ,c.user_id is null as is_default_workout
        ,u.name as shared_from_name
	FROM workouts a
	JOIN workout_types b on b.id = a.workout_type_id
    LEFT JOIN user_workouts c on c.workout_id = a.id
    LEFT JOIN workout_shares ws on ws.accepted_workout_id = a.id and ws.receiver_user_id = '{user_id}' and ws.status = 'accepted'
    LEFT JOIN users u on u.id = ws.sender_user_id) aa
WHERE {lookup_col} = '{lookup_val}'
"""

q_get_workout_raw = """
SELECT
    id,
    name,
    workout_type_id,
    description,
    workout_data
FROM workouts
WHERE id = '{workout_id}' and deleted = 0
"""

q_create_workout = """
INSERT INTO workouts (id, name, workout_type_id, description, workout_data)
VALUES (:id, :name, :workout_type_id, :description, :workout_data)
"""

q_delete_workout = """
UPDATE workouts
SET deleted = 1
WHERE id = '{workout_id}'
"""

q_update_workout_data = """
UPDATE workouts
SET workout_data = :workout_data
WHERE id = :id
"""

q_update_workout_meta = """
UPDATE workouts
SET name = :name,
    description = :description
WHERE id = :id
"""

q_update_assistant_message_actions = """
UPDATE assistant_messages
SET actions_json = :actions_json,
    action_results_json = :action_results_json
WHERE id = :id
"""

q_get_user_exercise_ids = """
SELECT
    exercise_id
FROM user_exercises
WHERE user_id = '{user_id}'
"""

q_get_exercise_ids_by_names = """
SELECT
    id,
    name
FROM exercises
WHERE name IN :names
  and deleted = 0
"""

q_create_workout_share = """
INSERT INTO workout_shares (id, sender_user_id, receiver_user_id, workout_snapshot, status, created_at)
VALUES (:id, :sender_user_id, :receiver_user_id, :workout_snapshot, :status, :created_at)
"""

q_get_pending_workout_shares = """
SELECT
    ws.id,
    ws.workout_snapshot,
    ws.created_at,
    u.name as sender_name,
    u.email as sender_email
FROM workout_shares ws
JOIN users u on u.id = ws.sender_user_id
WHERE ws.receiver_user_id = '{user_id}'
  AND ws.status = 'pending'
ORDER BY ws.created_at DESC
"""

q_get_workout_share = """
SELECT
    id,
    sender_user_id,
    receiver_user_id,
    workout_snapshot,
    status,
    created_at,
    responded_at,
    accepted_workout_id
FROM workout_shares
WHERE id = '{share_id}'
LIMIT 1
"""

q_update_workout_share_status = """
UPDATE workout_shares
SET status = :status,
    responded_at = :responded_at,
    accepted_workout_id = :accepted_workout_id
WHERE id = :id
"""

# queries for workout_logs
q_get_workout_logs_all = """
SELECT
	wl.id
	,w.name as workout_name
	,wl.feedback_data
    ,wl.completed_at
	,wl.created_at
FROM workout_logs wl
LEFT JOIN workouts w on w.id = wl.workout_id
WHERE wl.user_id = '{user_id}'  and wl.deleted = 0
"""

q_get_workout_log = """
SELECT
	wl.id
	,w.name as workout_name
	,wl.feedback_data
    ,wl.completed_at
	,wl.created_at
FROM workout_logs wl
JOIN workouts w on w.id = wl.workout_id
WHERE wl.id = '{id}'
"""

q_create_workout_log = """
INSERT INTO workout_logs (id, workout_id, user_id, feedback_data, completed_at, created_at)
VALUES (:id, :workout_id, :user_id, :feedback_data, :completed_at, :created_at)
"""

q_delete_workout_log = """
UPDATE workout_logs
SET deleted = 1
WHERE id = '{log_id}'
"""

# queries for user
q_create_user = """
INSERT INTO users(id, email, password_hash, created_at, name, status_id)
VALUES (:id, :email, :password_hash, :created_at, :name, :status_id)
"""

q_set_user_preferences = """
INSERT INTO user_preferences(user_id, show_all_workouts, assistant_mode)
VALUES( :user_id, :show_all_workouts, :assistant_mode)
"""

q_update_user = """
UPDATE users
set
    password_hash = :password_hash,
    status_id = 2
WHERE id = :id;
"""

q_get_user = """
SELECT
	a.id
	,a.email
	,a.created_at
    ,a.name
    ,b.name as status
FROM users a
JOIN user_status b on b.id = a.status_id
WHERE a.{lookup_col} = '{lookup_val}'
"""

q_get_user_by_email = """
SELECT
    id,
    email,
    name
FROM users
WHERE email = '{email}'
"""

q_get_user_auth = """
SELECT
	id
	,email
	,password_hash
FROM users
WHERE email = '{email}'
"""

q_get_user_preferences = """
SELECT
	user_id
    , show_all_workouts
    , assistant_mode
FROM user_preferences
WHERE user_id = '{user_id}'
"""

q_update_user_preferences_mode = """
UPDATE user_preferences
SET assistant_mode = :assistant_mode
WHERE user_id = :user_id
"""

# assistant messages
q_create_assistant_message = """
INSERT INTO assistant_messages (id, user_id, conversation_id, role, content, mode, actions_json, action_results_json, created_at)
VALUES (:id, :user_id, :conversation_id, :role, :content, :mode, :actions_json, :action_results_json, :created_at)
"""

q_get_assistant_messages = """
SELECT
    id,
    conversation_id,
    role,
    content,
    mode,
    actions_json,
    action_results_json,
    created_at
FROM assistant_messages
WHERE user_id = '{user_id}'
ORDER BY created_at DESC
LIMIT {limit}
"""

q_get_assistant_messages_by_conversation = """
SELECT
    id,
    conversation_id,
    role,
    content,
    mode,
    actions_json,
    action_results_json,
    created_at
FROM assistant_messages
WHERE user_id = '{user_id}'
  AND conversation_id = '{conversation_id}'
ORDER BY created_at DESC
LIMIT {limit}
"""

q_create_assistant_conversation = """
INSERT INTO assistant_conversations (id, user_id, title, created_at, updated_at)
VALUES (:id, :user_id, :title, :created_at, :updated_at)
"""

q_get_assistant_conversations = """
SELECT
    id,
    title,
    created_at,
    updated_at
FROM assistant_conversations
WHERE user_id = '{user_id}'
ORDER BY updated_at DESC
"""

q_update_assistant_conversation_title = """
UPDATE assistant_conversations
SET title = :title,
    updated_at = :updated_at
WHERE id = :id
"""

q_touch_assistant_conversation = """
UPDATE assistant_conversations
SET updated_at = :updated_at
WHERE id = :id
"""

q_get_latest_assistant_conversation = """
SELECT
    id,
    title,
    created_at,
    updated_at
FROM assistant_conversations
WHERE user_id = '{user_id}'
ORDER BY updated_at DESC
LIMIT 1
"""

q_get_assistant_conversation = """
SELECT
    id,
    title,
    created_at,
    updated_at
FROM assistant_conversations
WHERE id = '{conversation_id}'
  AND user_id = '{user_id}'
LIMIT 1
"""

q_update_assistant_messages_conversation_for_user = """
UPDATE assistant_messages
SET conversation_id = :conversation_id
WHERE user_id = :user_id
  AND (conversation_id IS NULL OR conversation_id = '')
"""

# queries for user_workout
q_create_user_workout = """
INSERT INTO user_workouts
VALUES (:user_id, :workout_id)
"""

# queries for user_exercise
q_create_user_exercise = """
INSERT INTO user_exercises
VALUES (:user_id, :exercise_id)
"""

# queries for user_reports
q_create_user_report = """
INSERT INTO user_reports(user_id, created_at, updated_at, report_name, filename)
VALUES (:user_id, :created_at, :updated_at, :report_name, :filename)
"""

q_get_user_reports = """
SELECT *
FROM user_reports
WHERE user_id = '{user_id}'
"""

q_update_user_reports = """
UPDATE user_reports
set
    filename = '{filename}',
    updated_at = '{updated_at}'
WHERE user_id = '{user_id}' and report_name = '{report_name}'
"""

# queries for dropdown lookup
q_get_muscle_groups_all = """
SELECT distinct id, name from muscle_group_names;
"""

q_get_exercise_types_all = """
SELECT distinct id, name from exercise_types;
"""

q_get_exercise_equipment_all = """
SELECT distinct id, name from exercise_equipment;
"""

q_get_exercises_by_names = """
SELECT
    name,
    video_slug
FROM exercises
WHERE deleted = 0
  AND name IN :names
"""

q_get_workout_types_all = """
SELECT distinct id, name from workout_types;
"""

# queries for password reset request

q_create_pass_reset_request = """
INSERT INTO password_reset_request(user_id, url_var, created_at)
VALUES(:user_id, :url_var, :created_at)
"""
q_get_pass_reset_user = """
SELECT *
FROM password_reset_request
WHERE url_var = '{url_var}'
"""
