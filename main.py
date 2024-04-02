from flask import Flask, render_template, request, flash, session, jsonify, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
from forms import RegistrationForm, LoginForm
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64decode
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


def load_private_key():
    try:
        with open('privatekey.pem', 'r') as file:
            key_contents = file.read()
            print("Private key contents:")
            print(key_contents)

            private_key = RSA.import_key(key_contents)
            return private_key
    except FileNotFoundError:
        print("Private key file not found!")
        return None
    except ValueError as e:
        print("Error loading private key:", e)
        return None


def decrypt_key(encrypted_key):
    try:
        private_key = load_private_key()
        if private_key is None:
            return None

        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        decrypted_key_bytes = cipher.decrypt(b64decode(encrypted_key))
        decrypted_key_str = decrypted_key_bytes.decode(
            'utf-8')
        print("The decrypted key-----------", decrypted_key_str)
        return decrypted_key_str
    except Exception as e:
        print("Error decrypting key:", e)
        return None


def decrypt_message(data: str, key: str, passedIv: str) -> str:
    secret_key = key
    iv = passedIv
    print(iv)
    ciphertext = b64decode(data)
    derived_key = b64decode(secret_key)
    cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode('utf-8'))
    decrypted_data = cipher.decrypt(ciphertext)
    return unpad(decrypted_data, 16).decode("utf-8")


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
        rooms[client_id] = {"code": code, "members": 0}
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
                 {"status": "Correct", "room_code": room_code}, room=room_code)
    else:
        emit('user-join-response', {"status": "Incorrect"})

    print("Room Content[AFTER JOIN ROOM]: ", rooms)


@socketio.on('send_message')
def handle_send_message(data):
    client_id = session.get("client_id")
    room = data["code"]
    if client_id not in rooms:
        return
    encrypted_message = data["message"]
    encrypted_key = data["key"]
    iv = data["iv"]
    print(f"[ENCRYPTED] key is {encrypted_key}")
    print(f"[ENCRYPTED] {client_id} said: {data['message']}")
    print(f"[ENCRYPTED] message type is ... {type(encrypted_message)}")
    decrypted_key = decrypt_key(encrypted_key)
    decrypted_message = decrypt_message(encrypted_message, decrypted_key, iv)
    emit('receive_message', {'message': decrypted_message}, room=room)
    print(f"[DECRYPTED] {client_id} said: {decrypted_message}")


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
                break


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=7000, debug=True)
