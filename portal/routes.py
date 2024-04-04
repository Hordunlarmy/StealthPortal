from flask import (Blueprint, render_template, request, flash,
                   session, jsonify, redirect, url_for)
from flask_bcrypt import Bcrypt
from .engine.db_storage import User, Message, load_user
from .forms import RegistrationForm, LoginForm
from .crypto import generate_secret_word
import portal
import uuid

main = Blueprint("main", __name__, template_folder="templates")
bcrypt = Bcrypt()


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
    from portal import db
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(username=form.username.data,
                    email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created!'
              'You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main.route('/login', strict_slashes=False, methods=["post", "get"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if (user and
                bcrypt.check_password_hash(user.password, form.password.data)):
            login_user(user, remember=form.remember.data)
            # next_page = request.args.get('next')
    # return redirect(next_page) if next_page else redirect(url_for('home'))
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)
