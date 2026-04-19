import asyncio
from web_app.downloader import async_get_stream_info

async def test():
    info = await async_get_stream_info("https://www.youtube.com/watch?v=jNQXAC9IVRw")
    print(info)

asyncio.run(test())
