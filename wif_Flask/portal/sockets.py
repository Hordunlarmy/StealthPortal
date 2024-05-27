from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_login import current_user
from .engine.db_storage import User, Message, load_user
from .crypto import load_private_key, decrypt_key, decrypt_message
from .routes import session
import portal


# socketio = SocketIO(app, cors_allowed_origins="*")
socketio = SocketIO(cors_allowed_origins="*")


@socketio.on('connect')
def handle_connect():
    print(f"Client {session.get('client_id')} connected")


@socketio.on('handshake')
def handle_handshake(data):
    code = data['code']
    client_id = session.get('client_id')
    session['code'] = code
    join_room(code)
    if current_user.is_authenticated:
        user_id = current_user.id
        if user_id not in portal.authenticated_in_room:
            portal.authenticated_in_room[user_id] = code
        print(
            f" Authenticated users[HANDSHAKE] after join is {portal.authenticated_in_room}")

    if client_id not in portal.rooms:
        portal.rooms[client_id] = {"code": code, "members": 1}
    print("Room Content: ", portal.rooms)


@socketio.on('user-join')
def handle_user_join(data):
    room_code = data['code']
    all_code = []
    for room_id, room_data in portal.rooms.items():
        all_code.append(room_data['code'])

    if not room_code:
        emit('user-join-response', {"status": "Empty"})
        return

    if room_code in all_code:
        if room_code == session.get('code'):
            emit('user-join-response', {"status": "SelfCode"})
        else:
            join_room(room_code)
            if current_user.is_authenticated:
                user_id = current_user.id
                portal.authenticated_in_room[user_id] = room_code
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
    print(
        f" Authenticated users[USER_JOIN] after join is {portal.authenticated_in_room}")

    print("Room Content[AFTER JOIN ROOM]: ", portal.rooms)


@socketio.on('send_message')
def handle_send_message(data):
    from portal import db
    code = data["code"]
    client_id = session.get("client_id")
    if client_id not in portal.rooms:
        return
    sender_room = portal.rooms[client_id]['code']
    encrypted_message = data["message"]
    encrypted_key = data["key"]
    iv = data["iv"]
    print("authenticated???? ---- ", portal.authenticated_in_room)
    if portal.authenticated_in_room:
        for user_id, room_code in portal.authenticated_in_room.items():
            if room_code == code:
                new_message = Message(message=encrypted_message,
                                      key=encrypted_key, iv=iv,
                                      user_id=user_id)
                db.session.add(new_message)
                db.session.commit()
    decrypted_key = decrypt_key(encrypted_key)
    decrypted_message = decrypt_message(encrypted_message, decrypted_key, iv)
    emit('receive_message', {'message': decrypted_message,
         'sender': request.sid}, room=sender_room)
    print(
        f"[DECRYPTED] {client_id}[{request.sid}] said: "
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
        if current_user.is_authenticated:
            user_id = current_user.id
            if user_id in portal.authenticated_in_room:
                portal.authenticated_in_room.pop(user_id)
        print(
            f" Authenticated users[DISCONNECT] after disconnect is {portal.authenticated_in_room}")

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
