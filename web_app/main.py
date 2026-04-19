from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import sys
import os
import httpx
import urllib.parse

from .downloader import async_get_info, async_download, async_get_stream_info
from .stats import log_download, STATS_FILE

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")
templates = Jinja2Templates(directory="web_app/static")

class DownloadRequest(BaseModel):
    url: str
    format_id: str = "best[ext=mp4]/best"

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/api/info")
@limiter.limit("15/minute")
async def get_video_info(request: Request, req: DownloadRequest):
    info = await async_get_info(req.url)
    if info:
        return info
    return {"error": "Could not fetch info"}

@app.post("/api/download")
@limiter.limit("5/minute")
async def download_video(request: Request, req: DownloadRequest, background_tasks: BackgroundTasks):
    stream_info = await async_get_stream_info(req.url, req.format_id)
    if not stream_info or not stream_info.get('stream_url'):
        return {"error": "Failed to extract stream URL"}
    
    stream_url = stream_info['stream_url']
    title = stream_info.get('title', 'video')
    ext = stream_info.get('ext', 'mp4')
    platform = stream_info.get('platform', 'Unknown')
    
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    filename = f"{safe_title}.{ext}"

    # Use background tasks to not block the stream response creation
    background_tasks.add_task(log_download, platform, "web_user")

    http_headers = stream_info.get('http_headers', {})
    
    async def stream_generator():
        async with httpx.AsyncClient(follow_redirects=True, timeout=None, headers=http_headers) as client:
            async with client.stream("GET", stream_url) as response:
                async for chunk in response.aiter_bytes(chunk_size=1024 * 1024): # 1MB chunks
                    yield chunk

    encoded_filename = urllib.parse.quote(filename)
    headers = {
        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
    }

    return StreamingResponse(
        stream_generator(),
        media_type='application/octet-stream',
        headers=headers
    )

@app.get("/api/stats")
async def get_stats():
    import json
    import aiofiles
    if not os.path.exists(STATS_FILE):
        return {"error": "No stats found"}
    async with aiofiles.open(STATS_FILE, "r") as f:
        content = await f.read()
        return json.loads(content)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/proxy-image")
async def proxy_image(url: str):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code != 200:
                raise HTTPException(status_code=404)
            return Response(content=resp.content, media_type=resp.headers.get("Content-Type", "image/jpeg"))
    except Exception:
        raise HTTPException(status_code=500)
