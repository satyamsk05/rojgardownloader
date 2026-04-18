from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import sys
import os
import httpx

from .downloader import async_get_info, async_download
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
    info = await async_get_info(req.url)
    if not info:
        return {"error": "Failed to fetch info"}
    
    file_path = await async_download(req.url)
    if file_path and os.path.exists(file_path):
        log_download(info['platform'], "web_user")
        # Add background task to delete file after sending
        background_tasks.add_task(cleanup_file, file_path)
        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type='application/octet-stream'
        )
    return {"error": "Download failed"}

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
