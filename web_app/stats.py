import json
import os
import asyncio
import aiofiles
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
STATS_FILE = os.path.join(DATA_DIR, "stats.json")

stats_lock = asyncio.Lock()

async def load_stats():
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
        async with aiofiles.open(STATS_FILE, "w") as f:
            await f.write(json.dumps(initial_stats, indent=4))
    
    async with aiofiles.open(STATS_FILE, "r") as f:
        content = await f.read()
        return json.loads(content)

async def save_stats(stats_data):
    async with aiofiles.open(STATS_FILE, "w") as f:
        await f.write(json.dumps(stats_data, indent=4))

async def log_download(platform, user_id):
    async with stats_lock:
        stats = await load_stats()
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
        
        await save_stats(stats)
