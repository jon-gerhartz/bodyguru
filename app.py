from dotenv import load_dotenv
from flask import Flask, session as flask_session
import os
from routes import main

load_dotenv()
app = Flask(__name__)
app.register_blueprint(main)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')