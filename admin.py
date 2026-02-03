from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

from lib.crud import get_exercises_admin, get_exercise_types, update_exercise_video
from utils.app_functions import admin_required
from utils.storage import get_storage_config, get_s3_client, get_bucket_name


admin = Blueprint("admin", __name__)

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "mov", "avi", "webm", "mkv"}


def _allowed_video_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


@admin.route("/admin/exercise-videos", methods=["GET", "POST"])
@admin_required
def exercise_videos():
    if request.method == "POST":
        storage_config = get_storage_config()
        s3_client = get_s3_client(storage_config)
        bucket_name = get_bucket_name(storage_config)

        uploaded = 0
        skipped = 0

        for key, file in request.files.items():
            if not key.startswith("video_"):
                continue
            exercise_id = key.replace("video_", "", 1)
            if not file or file.filename == "":
                skipped += 1
                continue
            if not _allowed_video_file(file.filename):
                flash(f"Invalid video type for exercise {exercise_id}.", "error")
                continue

            filename = secure_filename(file.filename)
            object_key = f"workout_content/{filename}"
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=file.stream,
                ContentType=file.mimetype or "application/octet-stream",
            )
            update_exercise_video(exercise_id, filename)
            uploaded += 1

        flash(f"Uploaded {uploaded} video(s). Skipped {skipped} empty file(s).")
        return redirect(url_for("admin.exercise_videos"))

    exercises = get_exercises_admin().to_dict(orient="records")
    exercise_types = get_exercise_types().to_dict(orient="records")
    return render_template(
        "admin_exercise_videos.html",
        exercises=exercises,
        exercise_types=exercise_types,
    )
