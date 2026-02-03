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
    session['show_all_workouts'] = str(show_all_workouts)
    return redirect(url_for('main.dashboard', user_id=user_id))


@auth.route('/reset-password', methods=['GET', 'POST'])
def send_pass_reset():
    if request.method == 'GET':
        return render_template('reset_pass_request.html')
    else:
        email = session.get('user_email')
        user_id = session.get('user_id')
        if not email or not user_id:
            flash('Please use the forgot password form.', 'error')
            return redirect(url_for('auth.forgot_password'))
        url_var = send_reset_email(email)
        create_pass_reset_request(user_id, url_var)
        return redirect(url_for('auth.send_pass_reset'))


@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_pass_request.html', sent=False)
    else:
        email = request.form.get('email')
        if not email:
            flash('Please enter an email address.', 'error')
            return render_template('forgot_pass_request.html', sent=False)

        user_df = get_user_auth(email)
        if len(user_df.index) > 0:
            url_var = send_reset_email(email)
            user_id = user_df['id'][0]
            create_pass_reset_request(user_id, url_var)
        return render_template('forgot_pass_request.html', sent=True)


@auth.route('/reset-password/<var>', methods=['GET'])
def reset_password(var):
    if request.method == 'GET':
        return render_template('reset_pass.html', url_var=var)


@auth.route('/reset-password-submit', methods=['POST'])
def submit_pass_reset():
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    if not password or password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(request.referrer)

    url_var = request.form.get('url_var')
    if not url_var and request.referrer:
        referrer_list = request.referrer.split('/')
        if referrer_list:
            url_var = referrer_list[-1]
    if not url_var:
        flash('Invalid reset link.', 'error')
        return redirect(url_for('main.index'))

    hashed_password = generate_password_hash(password)
    request_df = get_pass_reset_user(url_var)
    if len(request_df.index) == 0:
        flash('Reset link is invalid or expired.', 'error')
        return redirect(url_for('main.index'))
    user_id = request_df['user_id'][0]
    update_pass(user_id, hashed_password)
    return redirect(url_for('main.dashboard', user_id=user_id))


@auth.route('/logout', methods=['GET'])
def logout():
    session.clear()
    session['authenticated'] = False
    return redirect(url_for('main.index'))
