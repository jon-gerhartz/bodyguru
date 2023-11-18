from lib.crud import get_user_auth, create_user
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.app_functions import generate_password_hash, check_password

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user_df = get_user_auth(email)
    password_hash = user_df['password_hash'][0]
    authenticated = check_password(password, password_hash)
    if authenticated:
        session['authenticated'] = True
        session['user_email'] = email
        user_id = user_df['id'][0]
        session['user_id'] = user_id
        return redirect(url_for('main.dashboard', user_id=user_id))
    else:
        return redirect(request.referrer)


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    hashed_password = generate_password_hash(password)
    user_id = create_user(email, hashed_password)
    session['authenticated'] = True
    session['user_email'] = email
    session['user_id'] = user_id
    return redirect(url_for('main.dashboard', user_id=user_id))


@auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    session['authenticated'] = False
    return redirect(url_for('main.index'))
