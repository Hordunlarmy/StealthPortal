import asyncio
import json
from typing import Annotated

from fastapi import APIRouter, Depends, Request, WebSocket
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketDisconnect

from .manager import ConnectionManager

try:
    from StealthPortal.wif_FastAPI.portal.engine import get_db, models
    from StealthPortal.wif_FastAPI.portal.security.auth import (
        TokenData, current_user, get_current_user)
    from StealthPortal.wif_FastAPI.portal.security.rsa import (decrypt_key,
                                                               decrypt_message)
except ImportError:
    from portal.engine import get_db, models
    from portal.security.auth import TokenData, current_user, get_current_user
    from portal.security.rsa import decrypt_key, decrypt_message


socket = APIRouter()
manager = ConnectionManager()
user_dependency = Annotated[TokenData, Depends(current_user)]


@socket.websocket("/portal/")
async def websocket_endpoint(
    websocket: WebSocket, db: Session = Depends(get_db)
):
    await websocket.accept()
    try:
        while True:
            the_token = websocket.cookies.get("access_token")
            if the_token is None:
                token = None
            else:
                schema, token = the_token.split()
            user_data = await get_current_user(token)
            user = await current_user(user_data)

            json_data = json.dumps({"keep_alive": "ping"})
            await websocket.send_text(json_data)
            data_str = await asyncio.wait_for(
                websocket.receive_text(), timeout=30
            )
            try:
                data = json.loads(data_str)
            except json.JSONDecodeError:
                print("Invalid JSON data received:", data_str)
                continue
            event_type = data.get("event")
            if data == "pong":
                continue
            if event_type == "secret-code":
                secret_code = data.get("code")
                print(f"Secret_code - {secret_code}")
                await manager.connect(secret_code, websocket)
            if event_type == "join":
                code = data.get("code")
                print(f"Code Entered - {code}")
                status = await manager.user_join(code, secret_code, websocket)
                await manager.verify_secret(code, status, websocket)
                if status == "CorrectCode":
                    secret_code = code
            if event_type == "encryption":
                code = data.get("code")
                encrypted_message = data.get("message")
                encrypted_key = data.get("key")
                iv = data.get("iv")
                if user:
                    print("-----authenticated------")
                    new_message = models.Message(
                        message=encrypted_message,
                        key=encrypted_key,
                        iv=iv,
                        user_id=user.id,
                    )
                    try:
                        db.add(new_message)
                        db.commit()
                        db.refresh(new_message)
                    except Exception as e:
                        db.rollback()
                        print(e)
                decrypted_key = decrypt_key(encrypted_key)
                decrypted_message = decrypt_message(
                    encrypted_message, decrypted_key, iv
                )
                await manager.send_message(code, decrypted_message, websocket)

            if event_type == "refresh":
                await manager.disconnect(secret_code, websocket)

    except WebSocketDisconnect:
        if secret_code:
            await manager.disconnect(secret_code, websocket)
        else:
            print("Can't disconnect, secret_code is None")
