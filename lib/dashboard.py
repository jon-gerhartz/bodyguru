from collections import Counter, defaultdict
from datetime import datetime, timedelta
import json


TIMEFRAME_OPTIONS = {
    7: "Last 7 days",
    30: "Last 30 days",
    90: "Last 90 days",
    180: "Last 180 days",
    365: "Last 365 days",
}

GRAIN_OPTIONS = {
    "daily": "Daily",
    "weekly": "Weekly",
    "monthly": "Monthly",
}


def _parse_dt(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    normalized = str(value).strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = normalized[:-1]
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt)
        except ValueError:
            continue
    return None


def _load_payload(raw):
    try:
        payload = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _bucket_start(dt_value, grain):
    if grain == "monthly":
        return datetime(dt_value.year, dt_value.month, 1)
    if grain == "weekly":
        return datetime(dt_value.year, dt_value.month, dt_value.day) - timedelta(days=dt_value.weekday())
    return datetime(dt_value.year, dt_value.month, dt_value.day)


def _bucket_label(dt_value, grain):
    if grain == "monthly":
        return dt_value.strftime("%Y-%m")
    return dt_value.strftime("%Y-%m-%d")


def _bucket_step(current, grain):
    if grain == "monthly":
        year = current.year + (1 if current.month == 12 else 0)
        month = 1 if current.month == 12 else current.month + 1
        return datetime(year, month, 1)
    if grain == "weekly":
        return current + timedelta(days=7)
    return current + timedelta(days=1)


def _completed_sessions(logs_df):
    sessions = []
    if logs_df is None or logs_df.empty:
        return sessions
    for _, row in logs_df.iterrows():
        payload = _load_payload(row.get("feedback_data"))
        status = payload.get("status")
        if status in {"in_progress", "paused"}:
            continue
        completed_at = _parse_dt(row.get("completed_at") or payload.get("finished_at"))
        if not completed_at:
            continue
        sessions.append({
            "id": row.get("id"),
            "workout_name": row.get("workout_name") or "Workout",
            "completed_at": completed_at,
            "duration_seconds": int(payload.get("active_duration_seconds") or 0),
            "completed_exercise_ids": [str(item) for item in payload.get("completed_exercise_ids", []) if str(item).strip()],
            "tabatas": payload.get("tabatas") or [],
            "notes": (payload.get("notes") or "").strip(),
        })
    sessions.sort(key=lambda item: item["completed_at"])
    return sessions


def _filter_sessions(sessions, timeframe_days):
    cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
    return [session for session in sessions if session["completed_at"] >= cutoff]


def _build_series(filtered_sessions, timeframe_days, grain, value_fn):
    now = datetime.utcnow()
    cutoff = now - timedelta(days=timeframe_days)
    start = _bucket_start(cutoff, grain)
    end = _bucket_start(now, grain)
    buckets = []
    current = start
    while current <= end:
        buckets.append(current)
        current = _bucket_step(current, grain)

    values = defaultdict(int)
    for session in filtered_sessions:
        bucket = _bucket_start(session["completed_at"], grain)
        values[bucket] += value_fn(session)

    labels = [_bucket_label(bucket, grain) for bucket in buckets]
    data = [values.get(bucket, 0) for bucket in buckets]
    return {"labels": labels, "data": data}


def _recent_workouts(filtered_sessions, exercise_lookup):
    rows = []
    for session in sorted(filtered_sessions, key=lambda item: item["completed_at"], reverse=True)[:10]:
        rows.append({
            "date": session["completed_at"].isoformat(),
            "duration_seconds": session["duration_seconds"],
            "exercise_count": len(session["completed_exercise_ids"]),
            "tabata_count": len(session["tabatas"]),
            "has_notes": bool(session["notes"]),
            "workout_name": session["workout_name"],
        })
    return rows


def _muscle_coverage(filtered_sessions, exercise_lookup):
    counter = Counter()
    for session in filtered_sessions:
        for exercise_id in session["completed_exercise_ids"]:
            exercise = exercise_lookup.get(exercise_id)
            muscle = exercise.get("muscle_group_name") if exercise else None
            if muscle:
                counter[muscle] += 1
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return {
        "labels": [label for label, _ in items],
        "data": [value for _, value in items],
    }


def _muscle_neglect(sessions, exercise_lookup):
    latest_by_group = {}
    for session in sessions:
        for exercise_id in session["completed_exercise_ids"]:
            exercise = exercise_lookup.get(exercise_id)
            muscle = exercise.get("muscle_group_name") if exercise else None
            if not muscle:
                continue
            last_seen = latest_by_group.get(muscle)
            if last_seen is None or session["completed_at"] > last_seen:
                latest_by_group[muscle] = session["completed_at"]

    all_groups = sorted({value.get("muscle_group_name") for value in exercise_lookup.values() if value.get("muscle_group_name")})
    now = datetime.utcnow().date()
    rows = []
    for group in all_groups:
        last_trained = latest_by_group.get(group)
        if last_trained is None:
            rows.append({
                "muscle_group": group,
                "last_trained_label": "Never",
                "days_since": None,
                "is_neglected": True,
            })
            continue
        days_since = (now - last_trained.date()).days
        rows.append({
            "muscle_group": group,
            "last_trained_label": f"{days_since} day{'s' if days_since != 1 else ''} ago",
            "days_since": days_since,
            "is_neglected": days_since > 7,
        })
    rows.sort(key=lambda item: (item["days_since"] is not None, -(item["days_since"] or 9999), item["muscle_group"]))
    return rows


def _tabata_metrics(filtered_sessions, timeframe_days, grain):
    total_sessions = 0
    total_rounds = 0
    total_work_seconds = 0
    for session in filtered_sessions:
        if not session["tabatas"]:
            continue
        total_sessions += len(session["tabatas"])
        for tabata in session["tabatas"]:
            rounds = int(tabata.get("rounds") or 0)
            work_seconds = int(tabata.get("work_seconds") or 0)
            total_rounds += rounds
            total_work_seconds += rounds * work_seconds

    trend = _build_series(filtered_sessions, timeframe_days, grain, lambda session: sum(int(t.get("rounds") or 0) for t in session["tabatas"]))
    return {
        "sessions": total_sessions,
        "rounds": total_rounds,
        "work_seconds": total_work_seconds,
        "trend": trend,
    }


def build_dashboard_context(logs_df, exercises_df, timeframe_days=7, grain="daily"):
    timeframe_days = timeframe_days if timeframe_days in TIMEFRAME_OPTIONS else 7
    grain = grain if grain in GRAIN_OPTIONS else "daily"

    exercise_lookup = {}
    if exercises_df is not None and not exercises_df.empty:
        for _, row in exercises_df.iterrows():
            exercise_lookup[str(row["id"])] = {
                "name": row.get("name"),
                "muscle_group_name": row.get("muscle_group_name"),
            }

    sessions = _completed_sessions(logs_df)
    filtered_sessions = _filter_sessions(sessions, timeframe_days)
    total_duration_seconds = sum(item["duration_seconds"] for item in filtered_sessions)
    workouts_completed = len(filtered_sessions)
    active_training_days = len({item["completed_at"].date() for item in filtered_sessions})
    average_duration_seconds = int(total_duration_seconds / workouts_completed) if workouts_completed else 0
    last_workout = max((item["completed_at"] for item in sessions), default=None)
    days_since_last_workout = (datetime.utcnow().date() - last_workout.date()).days if last_workout else None

    workout_trend = _build_series(filtered_sessions, timeframe_days, grain, lambda _: 1)
    duration_trend = _build_series(filtered_sessions, timeframe_days, grain, lambda session: int(session["duration_seconds"] / 60))
    muscle_coverage = _muscle_coverage(filtered_sessions, exercise_lookup)
    neglect_rows = _muscle_neglect(sessions, exercise_lookup)
    tabata_metrics = _tabata_metrics(filtered_sessions, timeframe_days, grain)

    return {
        "timeframe_days": timeframe_days,
        "grain": grain,
        "timeframe_options": [{"value": key, "label": label} for key, label in TIMEFRAME_OPTIONS.items()],
        "grain_options": [{"value": key, "label": label} for key, label in GRAIN_OPTIONS.items()],
        "summary": {
            "workouts_completed": workouts_completed,
            "active_training_days": active_training_days,
            "total_training_seconds": total_duration_seconds,
            "average_duration_seconds": average_duration_seconds,
            "days_since_last_workout": days_since_last_workout,
        },
        "workout_trend": workout_trend,
        "duration_trend": duration_trend,
        "muscle_coverage": muscle_coverage,
        "muscle_neglect": neglect_rows,
        "tabata_metrics": tabata_metrics,
        "recent_workouts": _recent_workouts(filtered_sessions, exercise_lookup),
    }
