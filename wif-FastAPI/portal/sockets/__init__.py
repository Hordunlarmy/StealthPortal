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
