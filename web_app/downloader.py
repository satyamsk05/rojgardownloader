import yt_dlp
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

class Downloader:
    def __init__(self, download_path="downloads"):
        self.download_path = download_path
        if not os.path.exists(download_path):
            os.makedirs(download_path)
            
    def get_info(self, url):
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Video'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', None),
                    'uploader': info.get('uploader', 'Unknown'),
                    'platform': info.get('extractor_key', 'Unknown'),
                    'url': url
                }
            except Exception as e:
                print(f"Error fetching info: {e}")
                return None

    def download(self, url):
        ydl_opts = {
            'format': 'best',
            'outtmpl': f'{self.download_path}/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
            except Exception as e:
                print(f"Error downloading: {e}")
                return None

    def get_stream_info(self, url, format_id='best[ext=mp4]/best'):
        ydl_opts = {
            'format': format_id,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Video'),
                    'stream_url': info.get('url'),
                    'ext': info.get('ext', 'mp4'),
                    'platform': info.get('extractor_key', 'Unknown'),
                    'http_headers': info.get('http_headers', {})
                }
            except Exception as e:
                print(f"Error fetching stream info: {e}")
                return None

# Async wrapper for bot usage
async def async_get_info(url):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, Downloader().get_info, url)

async def async_download(url):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, Downloader().download, url)

async def async_get_stream_info(url, format_id='best[ext=mp4]/best'):
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, Downloader().get_stream_info, url, format_id)
