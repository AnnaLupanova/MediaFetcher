from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
from typing import Optional
from pytubefix import Stream
from concurrent.futures import ThreadPoolExecutor
import os
import uvicorn
from pytubefix import YouTube
from pytubefix.cli import on_progress
from enum import Enum

app = FastAPI()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_URL = os.getenv('YOUTUBE_API_URL')

class VideoFormat(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv" 


async def get_video_data(video_id: str) -> dict:
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YOUTUBE_API_KEY
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(YOUTUBE_API_URL, params=params) as response:
            if response.status != 200:
                raise HTTPException(status_code=response.status)
            return await response.json()


def get_stream(link: str, fmt: Optional[VideoFormat]='mp4') -> Optional[Stream]:
    try:
        if fmt not in (format.value for format in VideoFormat):
            raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

        return YouTube(link, on_progress_callback=on_progress).streams.filter(subtype=fmt.value)\
                                                        .order_by("resolution").desc().first()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def fetch_video_info(link: str, fmt: Optional[str]=None):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool,get_stream, link, fmt)


@app.get("/get-video-data/{video_id}")
async def get_data_from_youtube(video_id: str):
    res = await get_video_data(video_id)
    if 'items' not in res or not res['items']:
        raise HTTPException(status_code=404, detail="Failed to fetch video data")
    return res['items'][0]


@app.get("/get-download-link/{video_id}")
async def get_metadata(video_id: str):
    link = f"https://www.youtube.com/watch?v={video_id}"
    res = await fetch_video_info(link)
    if not res:
        return HTTPException(status_code=404, detail="Failed to fetch video data")
    return res.url


@app.get("/get-download-link/{video_id}/{fmt_video}")
async def get_metadata(video_id: str, fmt_video: str):
    link = f"https://www.youtube.com/watch?v={video_id}"
    res = await fetch_video_info(link, fmt_video)
    if not res:
        return HTTPException(status_code=404, detail="Failed to fetch video data")
    return {
        "duration": res._monostate.duration,
        "filesize_mb": res._filesize_mb,
        "title": res._monostate.title,
        "url": res.url,
        "resolution": res.resolution
    }

if __name__ == "__main__":

    uvicorn.run("main:app")