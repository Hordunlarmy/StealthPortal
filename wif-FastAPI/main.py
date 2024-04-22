from fastapi import FastAPI, APIRouter, Request, WebSocket, HTTPException, Depends, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from base64 import b64decode
from Crypto.Util.Padding import unpad
from forms import RegistrationForm, LoginForm, UpdateProfileForm
from engine import models
from engine import get_db, create_db
from sqlalchemy.orm import Session
from auth import TokenData, Token, login_user, current_user, logout_user, verify_passwd
from typing import Annotated
import uvicorn
import random
import uuid
import json


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

create_db()
user_dependency = Annotated[TokenData, Depends(current_user)]


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, WebSocket] = {}

    async def connect(self, secret_code: str, websocket: WebSocket):
        if secret_code not in self.rooms:
            self.rooms[secret_code] = []
        self.rooms[secret_code].append(websocket)
        print(f"Room Content - {self.rooms}")

    async def user_join(self, secret_code: str, owner_code: str,  websocket: WebSocket):
        if not secret_code:
            print("Empty code entered")
            return "Empty"

        room = self.rooms.get(secret_code)
        if room is None or owner_code not in self.rooms:
            print("Incorrect code entered")
            return "IncorrectCode"

        if websocket in room:
            print("User is already in the room")
            return "SelfCode"

        room.append(websocket)
        del self.rooms[owner_code]
        print(f"User joined room with secret code {secret_code}")
        print(f"Room Content - {self.rooms}")
        return "CorrectCode"

    async def verify_secret(self, code: str, status: str, websocket: WebSocket):
        data = {"kind": "Verify", "status": status, "code": code}
        json_data = json.dumps(data)
        if status == "CorrectCode":
            if code in self.rooms:
                for ws in self.rooms[code]:
                    await ws.send_text(json_data)
        else:
            await websocket.send_text(json_data)

    async def send_message(self, code: str, message: str, websocket: WebSocket):
        if code in self.rooms:
            for ws in self.rooms[code]:
                sender = "isYou"
                if ws == websocket:
                    sender = "isMe"
                await ws.send_text(json.dumps({"kind": "messageSubmit", "sender": sender, "message": message}))
        else:
            print(f"Can't send message. wrong room code {code}")

    async def disconnect(self, secret_code: str, websocket: WebSocket):
        if secret_code in self.rooms:
            if websocket in self.rooms[secret_code]:
                self.rooms[secret_code].remove(websocket)
                if len(self.rooms[secret_code]) <= 1:
                    data = {"kind": "refresh", "status": "Reset"}
                    json_data = json.dumps(data)
                    for ws in self.rooms[secret_code]:
                        await ws.send_text(json_data)
                print(f"WebSocket removed from room {secret_code}")
                if not self.rooms[secret_code]:
                    del self.rooms[secret_code]
                    print(f"Room {secret_code} is empty and deleted")
            else:
                print("WebSocket not found in room")
        else:
            print("Room not found")


manager = ConnectionManager()


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


def load_private_key():
    try:
        with open('privatekey.pem', 'r') as file:
            key_contents = file.read()
            private_key = RSA.import_key(key_contents)
            return private_key
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail="Private key file not found!")
    except ValueError as e:
        raise HTTPException(
            status_code=500, detail=f"Error loading private key: {e}")


def decrypt_key(encrypted_key):
    try:
        private_key = load_private_key()
        cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
        decrypted_key_bytes = cipher.decrypt(b64decode(encrypted_key))
        decrypted_key_str = decrypted_key_bytes.decode()
        return decrypted_key_str
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decrypting key: {e}")


def decrypt_message(data: str, key: str, passedIv: str):
    try:
        secret_key = key
        iv = passedIv
        ciphertext = b64decode(data)
        derived_key = b64decode(secret_key)
        cipher = AES.new(derived_key, AES.MODE_CBC, iv.encode('utf-8'))
        decrypted_data = cipher.decrypt(ciphertext)
        unpad_data = unpad(decrypted_data, 16).decode("utf-8")
        return unpad_data
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error decrypting message: {e}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data_str = await websocket.receive_text()
            # Parse JSON data
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


@app.get("/")
async def index(request: Request):
    code = generate_secret_word(5)
    return templates.TemplateResponse(
        "index.html", {"request": request, "code": code, "title": "Home", "current_user": user_dependency})


@app.get("/about")
async def about(request: Request):
    return templates.TemplateResponse("about.html", {"request": request, "title": "About", "current_user": user_dependency})


@app.get("/register")
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    from auth import hash_passwd
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        hashed_password = hash_passwd(form.password.data.encode('utf-8'))
        user = models.User(username=form.username.data,
                           email=form.email.data, password=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)

        # flash(f'Account created for {form.username.data}!', 'success')
        return templates.TemplateResponse("index.html", {"request": request})
    return templates.TemplateResponse("register.html", {"request": request, "title": 'Register', "form": form, "current_user": user_dependency})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    form = await LoginForm.from_formdata(request)
    return templates.TemplateResponse("login.html", {"request": request, "title": 'Login', "form": form, "current_user": user_dependency})


@app.post("/login")
async def post_login(request: Request, response: Response, db: Session = Depends(get_db)):
    form = await LoginForm.from_formdata(request)

    if await form.validate_on_submit():
        user = db.query(models.User).filter(
            models.User.email == form.email.data).first()

        if user and verify_passwd(form.password.data.encode('utf-8'), user.password):
            # Process login
            token_data = await login_user(response, user, remember=form.remember.data)
            print("User logged in successfully, redirecting to home...")
            # Redirect to the home page after successful login
            return token_data


@app.get("/logout")
async def logout(response: Response, user: current_user):
    await logout_user(response)
    return RedirectResponse(url="/home", status_code=303)


@app.get('/profile', response_class=HTMLResponse)
async def profile(request: Request, user: user_dependency, db: Session = Depends(get_db)):
    form = UpdateProfileForm()  # Assume default is GET
    form.username = current_user.username
    form.email = current_user.email
    return templates.TemplateResponse('profile.html', {"request": request, "form": form, "title": "Profile", "current_user": current_user})


@app.post('/profile', response_class=HTMLResponse)
async def profile_post(request: Request, user: user_dependency, db: Session = Depends(get_db)):
    form = UpdateProfileForm(await request.form())
    if form.validate():  # Implement validation method or use Pydantic validation
        current_user.username = form.username
        current_user.email = form.email
        db.commit()
        # FastAPI doesn't support Flask's flash; use alternative like session cookies or frontend handling
        return RedirectResponse(url='/profile', status_code=status.HTTP_303_SEE_OTHER)


@app.get('/history', response_class=HTMLResponse)
async def history(request: Request, user: user_dependency, db: Session = Depends(get_db)):
    current_user = user
    messages = db.query(models.Message).filter_by(
        user_id=current_user.id).all()
    user_messages = {}
    for message in messages:
        decrypted_key = decrypt_key(message.key)
        decrypted_message = decrypt_message(
            message.message, decrypted_key, message.iv)
        user_messages[message.id] = decrypted_message
    return templates.TemplateResponse('history.html', {"request": request, "messages": user_messages, "title": "History", "current_user": current_user})


@app.get('/delete', response_class=HTMLResponse)
async def delete_message(request: Request, user: user_dependency, db: Session = Depends(get_db)):
    return {"detail": "Deleted"}

if __name__ == "__main__":
    uvicorn.run("main:app", reload="True")
