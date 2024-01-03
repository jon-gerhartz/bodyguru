from dotenv import load_dotenv
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from utils.app_functions import gen_random

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")


def send_email(to_email, template_id, **kwargs):
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=to_email
    )

    dynamic_template_data = {}

    message.template_id = template_id
    if 'url_base' in kwargs.keys():
        dynamic_template_data['url_base'] = kwargs['url_base']

    if 'url_var' in kwargs.keys():
        dynamic_template_data['url_var'] = kwargs['url_var']

    print(dynamic_template_data)
    message.dynamic_template_data = dynamic_template_data

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)


PASS_RESET_TEMPLATE_ID = os.getenv("PASS_RESET_TEMPLATE_ID")
BASE_DOMAIN = os.getenv("BASE_DOMAIN")


def send_reset_email(to_email):
    url_var = gen_random(20)
    send_email(to_email, PASS_RESET_TEMPLATE_ID,
               url_base=BASE_DOMAIN, url_var=url_var)
    return url_var
