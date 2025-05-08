from flask import Blueprint, render_template, redirect, url_for
from flask_login import current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('login.html')

@auth_bp.route('/register')
def register():
    if current_user.is_authenticated:
        return redirect('/')
    return render_template('signup.html')