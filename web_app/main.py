import sys
import os
import asyncio
import urllib.parse

from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response, StreamingResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import httpx

from .downloader import async_get_info, async_get_stream_info
from .stats import log_download, STATS_FILE

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.mount("/static", StaticFiles(directory="web_app/static"), name="static")
templates = Jinja2Templates(directory="web_app/static")

class DownloadRequest(BaseModel):
    url: str
    format_id: str = "auto"

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

@app.get("/api/download")
@limiter.limit("5/minute")
async def download_video(
    request: Request,
    background_tasks: BackgroundTasks,
    url: str,
    format_id: str = "auto"
):
    stream_info = await async_get_stream_info(url, format_id)
    if not stream_info:
        raise HTTPException(status_code=500, detail="Could not extract stream info")

    title = stream_info.get('title', 'video')
    platform = stream_info.get('platform', 'Unknown')
    needs_server = stream_info.get('needs_server', False)
    stream_url = stream_info.get('stream_url')
    http_headers = stream_info.get('http_headers', {})
    resolved_fmt = stream_info.get('resolved_format_id', format_id)

    safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
    background_tasks.add_task(log_download, platform, "web_user")

    # ── PATH A: Direct HTTPS stream available ──────────────────────────────────
    # Proxy the stream through our server using httpx to force a file download.
    # This keeps disk usage at 0 while ensuring it actually downloads instead of playing in a new tab.
    if not needs_server and stream_url:
        ext = 'mp4'
        filename = f"{safe_title}.{ext}"
        encoded_filename = urllib.parse.quote(filename)
        headers = {'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'}
        
        async def httpx_stream():
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", stream_url, headers=http_headers) as response:
                    async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                        yield chunk
                        
        return StreamingResponse(
            httpx_stream(), 
            media_type='application/octet-stream', 
            headers=headers
        )

    # ── PATH B: HLS / DASH / merge needed ─────────────────────────────────────
    # Use yt-dlp subprocess piped to stdout → StreamingResponse.
    # Nothing is written to disk; data flows directly to the browser.
    ext = 'mp4'
    filename = f"{safe_title}.{ext}"
    encoded_filename = urllib.parse.quote(filename)

    cookies_args = ['--cookies', 'cookies.txt'] if os.path.exists('cookies.txt') else []
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '-f', resolved_fmt,
        '--merge-output-format', 'mp4',
        '-o', '-',                  # pipe output to stdout
        '--no-playlist',
        '--quiet',
        *cookies_args,
        url,
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def stream_proc():
        try:
            while True:
                chunk = await proc.stdout.read(512 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    return StreamingResponse(
        stream_proc(),
        media_type='application/octet-stream',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
        }
    )

@app.get("/api/stats")
async def get_stats():
    import json, aiofiles
    if not os.path.exists(STATS_FILE):
        return {"error": "No stats found"}
    async with aiofiles.open(STATS_FILE, "r") as f:
        return json.loads(await f.read())

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
