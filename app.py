from auth import auth
from dotenv import load_dotenv
from flask import Flask, session as flask_session
import os
from routes import main
from utils.template_filters import fmt_dt, fmt_dt_str


load_dotenv()
app = Flask(__name__)
app.register_blueprint(main)
app.register_blueprint(auth)
# application secret
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
# API key for protected video upload endpoint
app.config['UPLOAD_API_KEY'] = os.getenv('UPLOAD_API_KEY')
app.add_template_filter(fmt_dt)
app.add_template_filter(fmt_dt_str)
