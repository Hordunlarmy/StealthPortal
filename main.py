from flask import Flask, render_template, request, flash, session, jsonify
from flask_socketio import SocketIO, emit
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


connected_clients = {}


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


def validate_secret(secret_word):
    for client_id, client_secret in connected_clients.items():
        if connected_clients[session.get('client_id')] == secret_word:
            return False
        return True
    return False


@app.route('/', strict_slashes=False, methods=["POST", "GET"])
@app.route('/home', strict_slashes=False, methods=["POST", "GET"])
def index():
    client_id = session.get('client_id')
    if request.method == "POST":
        submitted_code = request.form.get("code")
        connected_clients[client_id] = submitted_code
        print("Codes stored in session[POST]:", connected_clients)
        return render_template('index.html', submitted_code=submitted_code)

    code = generate_secret_word(5)
    connected_clients[client_id] = code
    print("Codes stored in session[GET]:", connected_clients)
    return render_template('index.html', code=code)


@app.route('/validate', strict_slashes=False, methods=["POST", "GET"])
def validate_code():
    submitted_code = request.json.get('code')
    connect_success = validate_secret(submitted_code)
    return jsonify({'connect_success': connect_success})


@app.before_request
def before_request():
    if 'client_id' not in session:
        session['client_id'] = str(uuid.uuid4())
    elif session['client_id'] not in connected_clients:
        session['client_id'] = str(uuid.uuid4())


@app.route('/register', strict_slashes=False, methods=["POST", "GET"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', strict_slashes=False, methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.email.data == 'admin@blog.com' and form.password.data == 'password':
            flash('You have been logged in!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password',
                  'danger')
    return render_template('login.html', form=form)


@socketio.on('connect')
def handle_connect():
    print(f"Client {session.get('client_id')} connected")
    connected_clients[session.get('client_id')] = None
    print("Codes stored in session[AFTER_CONNECT]:", connected_clients)


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client{ session.get('client_id')} disconnected")
    if session.get('client_id') in connected_clients:
        connected_clients.pop(session.get('client_id'))
    print("Codes stored in session[AFTER_DISCONNECT]:", connected_clients)


@socketio.on('handshake')
def handle_handshake(data):
    client_id = request.sid
    client_code = data['client_code']

    # Derive a key from the numeric code
    key = derive_key(client_code)

    # Store the key for the client
    connected_clients[client_id] = key

    emit('handshake_success', {'message': 'Handshake successful'})


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
