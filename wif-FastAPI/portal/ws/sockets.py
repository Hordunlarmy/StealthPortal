from fastapi import WebSocket, APIRouter
from starlette.websockets import WebSocketDisconnect
from portal.security.rsa import decrypt_key, decrypt_message
from .manager import ConnectionManager
import json


socket = APIRouter()
manager = ConnectionManager()


@socket.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_str = await websocket.receive_text()
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                print("Invalid JSON data received:", data_str)
                continue
            event_type = data.get("event")
            if event_type == "secret-code":
                secret_code = data.get("code")
                print(f"Secret_code - {secret_code}")
                await manager.connect(secret_code, websocket)
            if event_type == "join":
                code = data.get('code')
                print(f"Code Entered - {code}")
                status = await manager.user_join(code, secret_code, websocket)
                await manager.verify_secret(code, status, websocket)
                if status == "CorrectCode":
                    secret_code = code
            if event_type == "encryption":
                code = data.get('code')
                encrypted_message = data.get('message')
                encrypted_key = data.get('key')
                iv = data.get('iv')
                decrypted_key = decrypt_key(encrypted_key)
                decrypted_message = decrypt_message(
                    encrypted_message, decrypted_key, iv)
                await manager.send_message(code, decrypted_message, websocket)

            if event_type == 'refresh':
                await manager.disconnect(secret_code, websocket)

    except WebSocketDisconnect:
        if secret_code:
            await manager.disconnect(secret_code, websocket)
        else:
            print("Can't disconnect, secret_code is None")
