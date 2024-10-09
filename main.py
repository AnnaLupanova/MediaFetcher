import json

import aiohttp.client_exceptions
from fastapi import FastAPI, HTTPException, Path
import aiohttp
import asyncio
from typing import Optional
from pytubefix import Stream
from concurrent.futures import ThreadPoolExecutor
import os
import uvicorn
from pytubefix import YouTube, exceptions
from pytubefix.cli import on_progress
import re
from enum import Enum
from settings import AppSettings
from service.redis_service import RedisService
from contextlib import asynccontextmanager

app = FastAPI()
settings = AppSettings()
redis_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_pool
    try:
        redis_pool = RedisService.create_pool()
    except Exception as e:
        print(str(e))
    yield
    redis_pool.disconnect()


class VideoFormat(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv" 


async def get_video_data(video_id: str) -> dict:
    params = {
        "part": "snippet",
        "id": video_id,
        "key": settings.youtube_api_key
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.youtube_api_url, params=params) as response:
                result = await response.json()
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=result["error"]["message"])
                return result
    except aiohttp.client_exceptions.ClientError:
        raise HTTPException(status_code=503, detail="Service youtube unavailable")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_stream(link: str, fmt: Optional[VideoFormat]=VideoFormat.MP4) -> Optional[Stream]:
    try:
        if fmt and fmt not in (format.value for format in VideoFormat):
            raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

        return YouTube(link, on_progress_callback=on_progress).streams.filter(subtype=fmt)\
                                                        .order_by("resolution").desc().first()

    except exceptions.VideoUnavailable:
        raise HTTPException(status_code=404, detail="Video not found")
    except HTTPException: 
        raise
    except Exception as e:
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        message = ansi_escape.sub('', str(e))
        raise HTTPException(status_code=400, detail=message)


async def fetch_video_info(link: str, fmt: Optional[str]='mp4'):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool,get_stream, link, fmt)
    

def is_valid(pattern: str,id: str) -> bool:
    regex = re.compile(pattern)
    results = regex.match(id)
    if not results:
        return False
    return True


@app.get("/get-video-data/{video_id}")
async def get_data_from_youtube(video_id: str):
    pattern = settings.youtube_video_id_pattern
    if not is_valid(pattern, video_id):
        raise HTTPException(status_code=400, detail=f"Video id don't match pattern={pattern}")
    res = await get_video_data(video_id)
    if 'items' not in res or not res['items']:
        raise HTTPException(status_code=404, detail=f"Video with id {video_id} not found")
    return res['items'][0]


@app.get("/get-download-link/{video_id}")
async def get_metadata(video_id: str):
    link = f"https://www.youtube.com/watch?v={video_id}"
    if redis_pool:
        redis = RedisService(pool=redis_pool)
        cache = await redis.get_cache(key=f"{video_id}&mp4")
        if cache:
            return cache.decode()
    res = await fetch_video_info(link)
    if redis_pool:
        await redis.set_cache(key=f"{video_id}&mp4", value=res.url, expire=120)
    return res.url


@app.get("/get-download-link/{video_id}/{fmt_video}")
async def get_metadata_with_fmt(video_id: str, fmt_video: str):
    link = f"https://www.youtube.com/watch?v={video_id}"
    if redis_pool:
        redis = RedisService(pool=redis_pool)
        cache = await redis.get_cache(key=f"{video_id}&{fmt_video}")
        if cache:
            return json.loads(cache.decode())

    res = await fetch_video_info(link, fmt_video)
    result = {
        "duration": res._monostate.duration,
        "filesize_mb": res._filesize_mb,
        "title": res._monostate.title,
        "url": res.url,
        "resolution": res.resolution
    }
    if redis_pool:
        await redis.set_cache(key=f"{video_id}&{fmt_video}", value=json.dumps(result), expire=120)
    return result




