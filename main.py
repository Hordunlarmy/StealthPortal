from flask import Flask, render_template, request, flash, session, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from forms import RegistrationForm, LoginForm
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from datetime import timedelta
import uuid
import os
import base64
import json
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'c0851757a345207ea1e92661138d847b'
socketio = SocketIO(app, cors_allowed_origins="*")

rooms = {}


@app.before_request
def before_request():
    if 'client_id' not in session:
        session['client_id'] = str(uuid.uuid4())
    elif session['client_id'] not in rooms:
        session['client_id'] = str(uuid.uuid4())


def generate_secret_word(length):
    vowels = 'aeiou'
    consonants = 'bcdfghjklmnpqrstvwxyz'
    secret_word = ''

    for i in range(length):
        if i % 2 == 0:
            secret_word += random.choice(consonants)
        else:
            secret_word += random.choice(vowels)

    return secret_word


@app.route('/', strict_slashes=False, methods=["POST", "GET"])
@app.route('/home', strict_slashes=False, methods=["POST", "GET"])
def index():
    code = generate_secret_word(5)
    return render_template('index.html', code=code)


@app.route('/clear_session')
def clear_session():
    session.clear()
    return redirect(url_for('index'))


@app.route('/register', strict_slashes=False, methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('index'))  # Redirect to appropriate route
    return render_template('register.html', form=form)


@app.route('/login', strict_slashes=False, methods=["POST", "GET"])
def login():
    session.clear()
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))  # Redirect to appropriate route
        else:
            flash('Login Unsuccessful. Please check username and password',
                  'danger')
    return render_template('login.html', form=form)


@socketio.on('connect')
def handle_connect():
    print(f"Client {session.get('client_id')} connected")


@socketio.on('handshake')
def handle_handshake(data):
    code = data['code']
    client_id = session.get('client_id')
    session['code'] = code
    join_room(code)
    if client_id not in rooms:
        rooms[client_id] = {"code": code, "members": 0, "messages": []}
    rooms[client_id]["members"] += 1
    print("Room Content: ", rooms)


@socketio.on('user-join')
def handle_user_join(data):
    room_code = data['code']
    all_code = []
    for room_id, room_data in rooms.items():
        all_code.append(room_data['code'])

    if room_code in all_code:
        if room_code == session.get('code'):
            emit('user-join-response', {"status": "SelfCode"})
        else:
            join_room(room_code)
            rooms[session.get('client_id')]['code'] = room_code
            for room_id, room_data in rooms.items():
                if room_code == room_data["code"]:
                    room_data["members"] += 1
            emit('user-join-response',
                 {"status": "Correct"}, room=room_code)
    else:
        emit('user-join-response', {"status": "Incorrect"})

    print("Room Content[AFTER JOIN ROOM]: ", rooms)


@socketio.on('disconnect')
def handle_disconnect():
    client_id = session.get('client_id')
    room_code = rooms[client_id]['code']
    if client_id in rooms:
        leave_room(room_code)
        rooms.pop(client_id)
        print(f"Client {client_id} Disconnected")
        print("Room content [USERS REMAINING]:", rooms)
    else:
        print(f"Attempted to disconnect unknown client: {client_id}")

    for room_id, room_data in rooms.items():
        if room_code == room_data["code"]:
            room_data["members"] -= 1
            if room_data["members"] <= 1:
                emit('user-left-response',
                     {"members": "Reset"}, room=room_code)


@socketio.on('send_message')
def handle_send_message(data):
    sender_id = request.sid
    recipient_id = data['recipient_id']
    message = data['message']

    # Check if recipient is connected
    if recipient_id not in connected_clients:
        emit('error', {'message': 'Recipient is not connected'})
        return

    # Encrypt message using sender's key
    encrypted_message = encrypt_message(message, connected_clients[sender_id])

    # Decrypt message using recipient's key
    decrypted_message = decrypt_message(
        encrypted_message, connected_clients[recipient_id])

    # Broadcast the decrypted message to the recipient
    emit('receive_message', {'sender_id': sender_id,
         'message': decrypted_message}, room=recipient_id)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7000, debug=True)
