from fastapi import FastAPI, HTTPException
import asyncio
import aiohttp
import asyncio
import uvicorn
import os

app = FastAPI()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/videos"


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


@app.get("/get-video-data/{video_id}")
async def get_data_from_youtube(video_id: str):
    res = await get_video_data(video_id)
    if 'items' not in res or not res['items']:
        raise HTTPException(status_code=404, detail="Failed to fetch video data")
    return res['items'][0]

