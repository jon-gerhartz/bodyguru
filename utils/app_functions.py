import bcrypt
from functools import wraps
from flask import make_response, request, redirect, url_for, session

def generate_password_hash(password_raw):
	bytes_pw = password_raw.encode('utf-8')
	salt = bcrypt.gensalt(12)
	hash_val = bcrypt.hashpw(bytes_pw, salt)
	return hash_val

def check_password(password_raw, hash_val):
	bytes_pw = password_raw.encode('utf-8')
	result = bcrypt.checkpw(bytes_pw, hash_val)
	return result

def auth_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		if not session.get('authenticated'):
			return redirect(url_for('main.index'))
		return f(*args, **kwargs)
	return decorated