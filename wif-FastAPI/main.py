from fastapi import FastAPI, APIRouter, Request, WebSocket, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP, AES
from Crypto.Hash import SHA256
from base64 import b64decode
from Crypto.Util.Padding import unpad
from forms import RegistrationForm, LoginForm, UpdateProfileForm
import random
import uuid
import json


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
template = Jinja2Templates(directory="templates")


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
    return template.TemplateResponse(
        "index.html", {"request": request, "code": code, "title": "Home"})


@app.get("/about")
async def about(request: Request):
    return template.TemplateResponse("about.html", {"request": request, "title": "About"})


@app.get("/register")
@app.post("/register", response_class=HTMLResponse)
async def register(request: Request):
    form = await RegistrationForm.from_formdata(request)
    if await form.validate_on_submit():
        # flash(f'Account created for {form.username.data}!', 'success')
        return template.TemplateResponse("index.html", {"request": request})
    return template.TemplateResponse("register.html", {"request": request, "title": 'Register', "form": form})


@app.get("/login")
@app.post("/login", response_class=HTMLResponse)
async def login(request: Request):
    form = await LoginForm.from_formdata(request)
    if await form.validate_on_submit():
        # flash('You have been logged in!', 'success')
        return template.TemplateResponse("index.html", {"request": request})
    # flash('Login Unsuccessful. Please check username and password', 'danger')
    return template.TemplateResponse("login.html", {"request": request, "title": 'Login', "form": form})
