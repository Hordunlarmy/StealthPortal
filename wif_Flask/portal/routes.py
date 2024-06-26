from flask import (Blueprint, render_template, request, flash,
                   session, jsonify, redirect, url_for)
from flask_login import (login_user, current_user, logout_user, login_required)
from flask_bcrypt import Bcrypt
from .engine.db_storage import User, Message, load_user
from .forms import RegistrationForm, LoginForm, UpdateProfileForm
from .crypto import generate_secret_word, decrypt_key, decrypt_message
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
def home():
    return "HOME PAGE"


@main.route('/portal', strict_slashes=False, methods=["POST", "GET"])
def index():
    if current_user.is_authenticated:
        authenticated = True
        print(f"---- {session.get('client_id')} is Authenticated----")
    else:
        authenticated = False
        print(f"----{session.get('client_id')} is not Authenticated----")
    code = generate_secret_word(5)
    return render_template('index.html', code=code)


@main.route('/portal/register', strict_slashes=False, methods=["POST", "GET"])
def register():
    from portal import db
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
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


@main.route('/portal/login', strict_slashes=False, methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if (user and
                bcrypt.check_password_hash(user.password, form.password.data)):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.login'))
            return redirect(url_for('main.index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@main.route('/portal/logout', strict_slashes=False)
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@main.route('/portal/profile', strict_slashes=False, methods=["POST", "GET"])
@login_required
def profile():
    from portal import db
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('main.profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    return render_template('profile.html', title='Profile', form=form)


@main.route('/portal/history', strict_slashes=False, methods=["POST", "GET"])
@login_required
def history():
    user_id = current_user.id
    messages = Message.query.filter_by(user_id=user_id).all()
    user_messages = {}
    for message in messages:
        decrypted_key = decrypt_key(message.key)
        decrypted_message = decrypt_message(
            message.message, decrypted_key, message.iv)
        user_messages[message.id] = decrypted_message
    return render_template(
        'history.html', title='History', messages=user_messages)


@main.route('/portal/delete', strict_slashes=False, methods=["POST", "GET"])
@login_required
def delete_message():
    from portal import db
    message_ids = request.form.getlist('message_ids')
    for message_id in message_ids:
        message = Message.query.get(message_id)
        if message:
            if message.user_id == current_user.id:
                db.session.delete(message)
        db.session.commit()
    return redirect(url_for('main.history'))


@main.route('/portal/about', strict_slashes=False)
def about():
    return render_template('about.html', title='About')
