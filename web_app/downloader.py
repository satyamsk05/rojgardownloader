import yt_dlp
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

COOKIES = "cookies.txt"

def _base_opts():
    opts = {'quiet': True, 'no_warnings': True}
    if os.path.exists(COOKIES):
        opts['cookiefile'] = COOKIES
    return opts

class Downloader:
    def __init__(self):
        pass

    def get_info(self, url):
        """Fetch video metadata + list of available formats."""
        opts = _base_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)

                formats = []
                seen_heights = set()
                for f in (info.get('formats') or []):
                    height = f.get('height')
                    vcodec = f.get('vcodec', 'none')
                    if not height or vcodec == 'none':
                        continue
                    if height in seen_heights:
                        continue
                    seen_heights.add(height)

                    if height > 720:
                        fmt_str = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                        needs_merge = True
                    else:
                        fmt_str = f'best[height<={height}][ext=mp4]/bestvideo[height<={height}]+bestaudio/best[height<={height}]'
                        needs_merge = False

                    formats.append({
                        'format_id': fmt_str,
                        'height': height,
                        'label': f'{height}p',
                        'needs_merge': needs_merge,
                    })

                formats.sort(key=lambda x: x['height'], reverse=True)

                return {
                    'title': info.get('title', 'Video'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', None),
                    'uploader': info.get('uploader', 'Unknown'),
                    'platform': info.get('extractor_key', 'Unknown'),
                    'url': url,
                    'formats': formats,
                }
            except Exception as e:
                print(f"Error fetching info: {e}")
                return None

    def get_stream_info(self, url, format_id=None):
        """Extract stream URL. Returns direct URL + protocol so caller can decide how to serve."""
        instagram_urls = ('instagram.com', 'instagr.am')
        is_instagram = any(d in url for d in instagram_urls)

        if format_id is None or format_id == 'auto':
            if is_instagram:
                # Instagram: force direct HTTPS, avoid DASH
                format_id = 'best[ext=mp4][protocol!~=dash]/best[protocol!~=dash]/best'
            else:
                # All other sites: prefer direct HTTPS mp4, fall back to best
                # protocol=https filter gives us a direct URL we can redirect the browser to
                format_id = 'best[protocol=https][ext=mp4]/best[protocol=http][ext=mp4]/best[protocol=https]/best[protocol=http]/best'

        resolved_format_id = format_id
        opts = {**_base_opts(), 'format': format_id}

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                stream_url = info.get('url')
                protocol = info.get('protocol', '')

                # Detect if we need server-side processing
                # '+' = explicit DASH merge; m3u8/hls = HLS stream (multiple segments)
                needs_server = ('+' in format_id or
                                'm3u8' in protocol or
                                'hls' in protocol.lower())

                return {
                    'title': info.get('title', 'Video'),
                    'stream_url': stream_url,
                    'ext': info.get('ext', 'mp4'),
                    'platform': info.get('extractor_key', 'Unknown'),
                    'http_headers': info.get('http_headers', {}),
                    'protocol': protocol,
                    'needs_server': needs_server,
                    'resolved_format_id': resolved_format_id,
                }
            except Exception as e:
                print(f"Error fetching stream info: {e}")
                return None


async def async_get_info(url):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, Downloader().get_info, url)

async def async_get_stream_info(url, format_id=None):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, Downloader().get_stream_info, url, format_id)
