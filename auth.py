from lib.crud import get_user_auth, create_user, update_pass, create_pass_reset_request, get_pass_reset_user, get_user_preferences
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.app_functions import generate_password_hash, check_password
from lib.sendgrid import send_reset_email
import pandas as pd

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    user_df = get_user_auth(email)
    if len(user_df.index) == 0:
        flash(f'{email} is not found. Try signing up.', 'error')
        return redirect(url_for('main.index'))

    password_hash = user_df['password_hash'][0]
    authenticated = check_password(password, password_hash)
    if authenticated:
        session['authenticated'] = True
        session['user_email'] = email
        user_id = user_df['id'][0]
        session['user_id'] = user_id
        user_preferences = get_user_preferences(user_id)
        show_all_workouts = user_preferences['show_all_workouts'][0]
        session['show_all_workouts'] = str(show_all_workouts)
        return redirect(url_for('main.dashboard', user_id=user_id))
    else:
        flash(
            f'Password is incorrect for user: {email}. If you forgot your password, please email: jonathan@ideaship.io', 'error')
        return redirect(url_for('main.index'))


@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    hashed_password = generate_password_hash(password)
    try:
        if password:
            user_id = create_user(email, name, hashed_password, status_id=2)
        else:
            user_id = create_user(email, name, hashed_password)
    except Exception as e:
        flash(
            f'Account for {email} already exists. Try logging in. If you forgot your password, please email: jonathan@ideaship.io', 'error')
        print(e)
        return redirect(url_for('main.index'))
    session['authenticated'] = True
    session['user_email'] = email
    session['user_id'] = user_id
    user_preferences = get_user_preferences(user_id)
    show_all_workouts = user_preferences['show_all_workouts'][0]
    session['show_all_workouts'] = show_all_workouts
    return redirect(url_for('main.dashboard', user_id=user_id))


@auth.route('/reset-password', methods=['GET', 'POST'])
def send_pass_reset():
    if request.method == 'GET':
        return render_template('reset_pass_request.html')
    else:
        email = session['user_email']
        url_var = send_reset_email(email)
        user_id = session['user_id']
        create_pass_reset_request(user_id, url_var)
        return redirect(url_for('auth.send_pass_reset'))


@auth.route('/reset-password/<var>', methods=['GET'])
def reset_password(var):
    if request.method == 'GET':
        return render_template('reset_pass.html')


@auth.route('/reset-password-submit', methods=['POST'])
def submit_pass_reset():
    password = request.form.get('password')
    hashed_password = generate_password_hash(password)
    referrer_list = request.referrer.split('/')
    referrer_list_len = len(referrer_list)
    var = referrer_list[referrer_list_len-1]
    request_df = get_pass_reset_user(var)
    user_id = request_df['user_id'][0]
    update_pass(user_id, hashed_password)
    return redirect(url_for('main.dashboard', user_id=user_id))


@auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    session['authenticated'] = False
    return redirect(url_for('main.index'))
