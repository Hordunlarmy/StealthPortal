from flask import (Blueprint, render_template, request, flash,
                   session, jsonify, redirect, url_for)
from .forms import RegistrationForm, LoginForm
from .crypto import generate_secret_word
import portal
import uuid

main = Blueprint("main", __name__, template_folder="templates")


@main.before_request
def before_request():
    if 'client_id' not in session:
        session['client_id'] = str(uuid.uuid4())
    elif session['client_id'] not in portal.rooms:
        session['client_id'] = str(uuid.uuid4())


@main.route('/', strict_slashes=False, methods=["POST", "GET"])
@main.route('/home', strict_slashes=False, methods=["POST", "GET"])
def index():
    code = generate_secret_word(5)
    return render_template('index.html', code=code)


@main.route('/register', strict_slashes=False, methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)


@main.route('/login', strict_slashes=False, methods=["post", "get"])
def login():
    session.clear()
    form = loginform()
    if form.validate_on_submit():
        if (form.email.data == 'admin@blog.com'
                and form.password.data == 'password'):
            flash('you have been logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('login unsuccessful. please check username and password',
                  'danger')
    return render_template('login.html', form=form)
