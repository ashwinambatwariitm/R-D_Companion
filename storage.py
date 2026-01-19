import json, os, uuid
from datetime import datetime

FILE = "chats.json"

def load_chats():
    if os.path.exists(FILE):
        return json.load(open(FILE))
    return []

def save_chats(chats):
    json.dump(chats, open(FILE, "w"), indent=2)

def new_chat():
    return {
        "chat_id": str(uuid.uuid4()),
        "title": "New chat",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": []
    }
