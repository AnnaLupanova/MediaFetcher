from fastapi import FastAPI, HTTPException
import aiohttp
import asyncio
from typing import Optional
from pytubefix import Stream
from concurrent.futures import ThreadPoolExecutor
import os
from pytubefix import YouTube
from pytubefix.cli import on_progress

app = FastAPI()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_URL = os.getenv('YOUTUBE_API_URL')


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


def get_stream(link: str) -> Optional[Stream]:
    try:
        yt = YouTube(link, on_progress_callback=on_progress).streams.filter(subtype="mp4").order_by("resolution").desc().first()
        if not yt:
            raise HTTPException(status_code=404, detail="Failed to fetch video data")
        return yt
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


async def fetch_video_info(link: str):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool,get_stream, link)


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
    return res.url


