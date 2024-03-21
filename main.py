from flask import Flask, render_template, request, flash, session
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

# Key derivation function


def derive_key(code):
    salt = b'salt_123'
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        iterations=100000,
        salt=salt,
        length=32,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(str(code).encode()))
    return key

# Encrypt message


def encrypt_message(message, key):
    cipher = Cipher(algorithms.AES(key), modes.CFB8(),
                    backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(message.encode()) + encryptor.finalize()
    return base64.urlsafe_b64encode(ciphertext).decode()

# Decrypt message


def decrypt_message(encrypted_message, key):
    cipher = Cipher(algorithms.AES(key), modes.CFB8(),
                    backend=default_backend())
    decryptor = cipher.decryptor()
    ciphertext = base64.urlsafe_b64decode(encrypted_message)
    decrypted_message = decryptor.update(ciphertext) + decryptor.finalize()
    return decrypted_message.decode()


connected_clients = {}

# Generate a random code for the handshake
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
        if client_secret == secret_word:
            return True
        return False

@app.route('/', strict_slashes=False, methods=["POST", "GET"])
@app.route('/home', strict_slashes=False, methods=["POST", "GET"])
def index():
    client_id = session.get('client_id')
    if request.method == "POST":
        submitted_code = request.form.get("code")
        connect_success = validate_secret(submitted_code)

        connected_clients[client_id] = submitted_code
        print("Codes stored in session:", connected_clients)

        return render_template('index.html', code=submitted_code, connect_success=connect_success)
    code = generate_secret_word(5)
    
    connected_clients[client_id] = code

    print("Codes stored in session:", connected_clients)

    return render_template('index.html', code=code)


@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)
    session.modified = True
    if 'client_id' not in session:
        session['client_id'] = str(uuid.uuid4())


@app.route('/clear_session')
def clear_session():
    session.clear()
    return 'Session cleared'

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
    print(f"Client {request.sid} connected")


@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client {request.sid} disconnected")
    connected_clients.pop(request.sid, None)


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
