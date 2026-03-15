from dotenv import load_dotenv
import os
import resend
from utils.app_functions import gen_random

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL") or os.getenv("FROM_EMAIL")
BASE_DOMAIN = os.getenv("BASE_DOMAIN")
WORKOUT_INVITE_TEMPLATE_ID = os.getenv("RESEND_WORKOUT_INVITE_TEMPLATE_ID")

resend.api_key = RESEND_API_KEY


def send_email(to_email, subject, html, text):
    params = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    return resend.Emails.send(params)


def send_template_email(to_email, template_id, variables, subject=None):
    params = {
        "from": FROM_EMAIL,
        "to": [to_email],
        "template": {
            "id": template_id,
            "variables": variables,
        },
    }
    if subject:
        params["subject"] = subject
    return resend.Emails.send(params)


def send_reset_email(to_email):
    url_var = gen_random(20)
    reset_url = f"{BASE_DOMAIN}/reset-password/{url_var}"
    subject = "Reset your BodyGuru password"
    html = (
        "<p>You requested a password reset for BodyGuru.</p>"
        f"<p><a href=\"{reset_url}\">Reset your password</a></p>"
        "<p>If you did not request this, you can ignore this email.</p>"
    )
    text = (
        "You requested a password reset for BodyGuru.\n\n"
        f"Reset your password: {reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    send_email(to_email, subject, html, text)
    return url_var


def send_workout_invite_email(to_email, friend_first_name, workout_snapshot):
    if not WORKOUT_INVITE_TEMPLATE_ID:
        raise ValueError("RESEND_WORKOUT_INVITE_TEMPLATE_ID is not configured.")
    invite_url = workout_snapshot.get("invite_url", "")
    variables = {
        "friend_first_name": friend_first_name,
        "invite_url": invite_url,
        "workout_name": workout_snapshot.get("name", ""),
    }
    subject = f"{friend_first_name} shared a workout with you"
    return send_template_email(
        to_email,
        WORKOUT_INVITE_TEMPLATE_ID,
        variables,
        subject=subject,
    )
