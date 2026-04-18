import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({"allowed": ADMIN_IDS, "admin": ADMIN_IDS}, f, indent=4)
    
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users_data):
    with open(USERS_FILE, "w") as f:
        json.dump(users_data, f, indent=4)

def is_allowed(user_id):
    users = load_users()
    return user_id in users.get("allowed", []) or user_id in ADMIN_IDS

def is_admin(user_id):
    users = load_users()
    return user_id in users.get("admin", []) or user_id in ADMIN_IDS
