from flask_socketio import SocketIO, emit, join_room, leave_room
from .crypto import load_private_key, decrypt_key, decrypt_message
from .routes import session
import portal


# socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO()


@socketio.on('connect')
def handle_connect():
    print(f"Client {session.get('client_id')} connected")


@socketio.on('handshake')
def handle_handshake(data):
    code = data['code']
    client_id = session.get('client_id')
    session['code'] = code
    join_room(code)
    if client_id not in portal.rooms:
        portal.rooms[client_id] = {"code": code, "members": 1}
    print("Room Content: ", portal.rooms)


@socketio.on('user-join')
def handle_user_join(data):
    room_code = data['code']
    all_code = []
    for room_id, room_data in portal.rooms.items():
        all_code.append(room_data['code'])

    if room_code in all_code:
        if room_code == session.get('code'):
            emit('user-join-response', {"status": "SelfCode"})
        else:
            join_room(room_code)
            portal.rooms[session.get('client_id')]['code'] = room_code
            room_member_count = sum(
                1 for room_data in portal.rooms.values()
                if room_data["code"] == room_code
            )
            for room_id, room_data in portal.rooms.items():
                if room_code == room_data["code"]:
                    room_data["members"] = room_member_count
            emit('user-join-response',
                 {"status": "Correct", "room_code": room_code}, room=room_code)
    else:
        emit('user-join-response', {"status": "Incorrect"})

    print("Room Content[AFTER JOIN ROOM]: ", portal.rooms)


@socketio.on('send_message')
def handle_send_message(data):
    client_id = session.get("client_id")
    if client_id not in portal.rooms:
        return

    sender_room = portal.rooms[client_id]['code']
    encrypted_message = data["message"]
    encrypted_key = data["key"]
    iv = data["iv"]
    decrypted_key = decrypt_key(encrypted_key)
    decrypted_message = decrypt_message(encrypted_message, decrypted_key, iv)
    emit('receive_message', {'message': decrypted_message}, room=sender_room)
    print(
        f"[DECRYPTED] {client_id} said: "
        f"{decrypted_message} in room {sender_room}"
    )


@socketio.on('disconnect')
def handle_disconnect():
    client_id = session.get('client_id')
    room_code = portal.rooms[client_id]['code']
    counter_decremented = False
    if client_id in portal.rooms:
        leave_room(room_code)
        portal.rooms.pop(client_id)
        print(f"Client {client_id} Disconnected")
        print("Room content [USERS REMAINING]:", portal.rooms)
    else:
        print(f"Attempted to disconnect unknown client: {client_id}")

    for room_id, room_data in portal.rooms.items():
        if room_code == room_data["code"]:
            room_data["members"] -= 1
            if room_data["members"] <= 1:
                emit('user-left-response',
                     {"members": "Reset"}, room=room_code)
                break
