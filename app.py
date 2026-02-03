from auth import auth
from admin import admin
from dotenv import load_dotenv
from flask import Flask, session as flask_session
import os
from routes import main
from utils.template_filters import fmt_dt, fmt_dt_str


load_dotenv()
app = Flask(__name__)
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(admin)
# application secret
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
# API key for protected video upload endpoint
app.config['UPLOAD_API_KEY'] = os.getenv('UPLOAD_API_KEY')
app.config['ADMIN_EMAIL'] = os.getenv('ADMIN_EMAIL', 'j_gerhartz@yahoo.com')
app.add_template_filter(fmt_dt)
app.add_template_filter(fmt_dt_str)
