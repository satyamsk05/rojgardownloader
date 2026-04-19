import yt_dlp
import os
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor

COOKIES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
COBALT_API = "http://127.0.0.1:9000"

# Platforms cobalt handles (bypasses cloud IP blocking)
COBALT_PLATFORMS = {
    'instagram.com', 'instagr.am',
    'tiktok.com', 'vm.tiktok.com',
    'twitter.com', 'x.com',
    'facebook.com', 'fb.watch',
    'reddit.com', 'redd.it',
    'pinterest.com', 'pin.it',
    'snapchat.com',
    'twitch.tv',
    'vimeo.com',
    'dailymotion.com',
    'soundcloud.com',
    'tumblr.com',
    'bilibili.com',
    'ok.ru',
    'rutube.ru',
}

def _is_cobalt_url(url: str) -> bool:
    url_lower = url.lower()
    return any(p in url_lower for p in COBALT_PLATFORMS)

def _base_yt_opts():
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'age_limit': 99,
    }
    if os.path.exists(COOKIES):
        opts['cookiefile'] = COOKIES
    return opts

def _detect_platform(url: str) -> str:
    url = url.lower()
    platforms = {
        'instagram': 'Instagram', 'tiktok': 'TikTok',
        'twitter': 'Twitter', 'x.com': 'Twitter',
        'facebook': 'Facebook', 'reddit': 'Reddit',
        'youtube': 'YouTube', 'youtu.be': 'YouTube',
        'vimeo': 'Vimeo', 'twitch': 'Twitch',
        'dailymotion': 'Dailymotion', 'pinterest': 'Pinterest',
    }
    for key, name in platforms.items():
        if key in url:
            return name
    return 'Unknown'


# ── COBALT (Instagram, TikTok, Twitter, Facebook etc.) ────

async def _cobalt_get_info(url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{COBALT_API}/",
                json={"url": url, "downloadMode": "auto", "videoQuality": "1080"},
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
            data = resp.json()
            if data.get("status") in ("tunnel", "redirect", "stream"):
                filename = data.get("filename", "video.mp4")
                return {
                    'title': filename.rsplit('.', 1)[0],
                    'duration': 0,
                    'thumbnail': None,
                    'uploader': 'Unknown',
                    'platform': _detect_platform(url),
                    'url': url,
                    'formats': [
                        {'format_id': 'cobalt_1080', 'height': 1080, 'label': '1080p', 'needs_merge': False},
                        {'format_id': 'cobalt_720',  'height': 720,  'label': '720p',  'needs_merge': False},
                        {'format_id': 'cobalt_480',  'height': 480,  'label': '480p',  'needs_merge': False},
                    ],
                    '_cobalt': True,
                }
            print(f"Cobalt error: {data.get('error', {}).get('code', 'unknown')}")
            return None
    except Exception as e:
        print(f"Cobalt info error: {e}")
        return None

async def _cobalt_get_stream(url: str, quality: str = "cobalt_1080") -> dict | None:
    q_map = {'cobalt_1080': '1080', 'cobalt_720': '720', 'cobalt_480': '480'}
    q = q_map.get(quality, '1080')
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{COBALT_API}/",
                json={"url": url, "downloadMode": "auto", "videoQuality": q},
                headers={"Accept": "application/json", "Content-Type": "application/json"}
            )
            data = resp.json()
            if data.get("status") in ("tunnel", "redirect", "stream"):
                return {
                    'title': data.get("filename", "video").rsplit('.', 1)[0],
                    'stream_url': data.get("url"),
                    'ext': 'mp4',
                    'platform': _detect_platform(url),
                    'http_headers': {},
                    'protocol': 'https',
                    'needs_server': data.get("status") == "tunnel",
                    'resolved_format_id': quality,
                    '_cobalt': True,
                }
            return None
    except Exception as e:
        print(f"Cobalt stream error: {e}")
        return None


# ── YT-DLP (YouTube + 1000s of other sites) ───────────────

def _ytdlp_get_info(url: str) -> dict | None:
    opts = _base_yt_opts()
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = []
            seen_heights = set()
            for f in (info.get('formats') or []):
                height = f.get('height')
                vcodec = f.get('vcodec', 'none')
                if not height or vcodec == 'none' or height in seen_heights:
                    continue
                seen_heights.add(height)
                needs_merge = height > 720
                fmt_str = (
                    f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                    if needs_merge else
                    f'best[height<={height}][ext=mp4]/bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                )
                formats.append({'format_id': fmt_str, 'height': height, 'label': f'{height}p', 'needs_merge': needs_merge})
            formats.sort(key=lambda x: x['height'], reverse=True)
            return {
                'title': info.get('title', 'Video'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'uploader': info.get('uploader', 'Unknown'),
                'platform': info.get('extractor_key', 'Unknown'),
                'url': url,
                'formats': formats,
            }
        except Exception as e:
            print(f"yt-dlp info error: {e}")
            return None

def _ytdlp_get_stream(url: str, format_id: str = None) -> dict | None:
    if not format_id or format_id == 'auto':
        format_id = 'best[protocol=https][ext=mp4]/best[protocol=http][ext=mp4]/best[protocol=https]/best'
    opts = {**_base_yt_opts(), 'format': format_id}
    with yt_dlp.YoutubeDL(opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            protocol = info.get('protocol', '')
            return {
                'title': info.get('title', 'Video'),
                'stream_url': info.get('url'),
                'ext': info.get('ext', 'mp4'),
                'platform': info.get('extractor_key', 'Unknown'),
                'http_headers': info.get('http_headers', {}),
                'protocol': protocol,
                'needs_server': '+' in format_id or 'm3u8' in protocol or 'hls' in protocol.lower(),
                'resolved_format_id': format_id,
            }
        except Exception as e:
            print(f"yt-dlp stream error: {e}")
            return None


# ── PUBLIC API (auto-routes to cobalt or yt-dlp) ──────────

async def async_get_info(url: str) -> dict | None:
    if _is_cobalt_url(url):
        result = await _cobalt_get_info(url)
        if result is not None:
            return result
        print("Cobalt info failed or unreachable, falling back to yt-dlp...")
        
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, _ytdlp_get_info, url)

async def async_get_stream_info(url: str, format_id: str = None) -> dict | None:
    if _is_cobalt_url(url):
        result = await _cobalt_get_stream(url, format_id or 'cobalt_1080')
        if result is not None:
            return result
        print("Cobalt stream failed or unreachable, falling back to yt-dlp...")
        
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, _ytdlp_get_stream, url, format_id)