from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sys
import os
import httpx
import urllib.parse

from .downloader import async_get_info, async_download, async_get_stream_info
from .stats import log_download

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="web_app/static"), name="static")
templates = Jinja2Templates(directory="web_app/static")

class DownloadRequest(BaseModel):
    url: str

def cleanup_file(path: str):
    if os.path.exists(path):
        os.remove(path)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.post("/api/info")
async def get_video_info(req: DownloadRequest):
    info = await async_get_info(req.url)
    if info:
        return info
    return {"error": "Could not fetch info"}

@app.post("/api/download")
async def download_video(req: DownloadRequest, background_tasks: BackgroundTasks):
    stream_info = await async_get_stream_info(req.url)
    if not stream_info or not stream_info.get('stream_url'):
        return {"error": "Failed to extract stream URL"}
    
    stream_url = stream_info['stream_url']
    title = stream_info.get('title', 'video')
    ext = stream_info.get('ext', 'mp4')
    platform = stream_info.get('platform', 'Unknown')
    
    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    filename = f"{safe_title}.{ext}"

    log_download(platform, "web_user")

    async def stream_generator():
        async with httpx.AsyncClient() as client:
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
