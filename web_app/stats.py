import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(BASE_DIR, "stats.json")

def load_stats():
    if not os.path.exists(STATS_FILE):
        initial_stats = {
            "total_downloads": 0,
            "today": {},
            "platforms": {
                "instagram": 0,
                "youtube": 0,
                "twitter": 0,
                "others": 0
            },
            "users": {}
        }
        with open(STATS_FILE, "w") as f:
            json.dump(initial_stats, f, indent=4)
    
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats_data):
    with open(STATS_FILE, "w") as f:
        json.dump(stats_data, f, indent=4)

def log_download(platform, user_id):
    stats = load_stats()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Update total
    stats["total_downloads"] += 1
    
    # Update today
    stats["today"][today_str] = stats["today"].get(today_str, 0) + 1
    
    # Update platform
    if platform.lower() in stats["platforms"]:
        stats["platforms"][platform.lower()] += 1
    else:
        stats["platforms"]["others"] += 1
        
    # Update user stats
    user_id_str = str(user_id)
    if user_id_str not in stats["users"]:
        stats["users"][user_id_str] = {"downloads": 0}
    stats["users"][user_id_str]["downloads"] += 1
    
    save_stats(stats)
