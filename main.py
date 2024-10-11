import json
from fastapi import FastAPI, HTTPException, Depends
import re
from settings import AppSettings
from service.redis_service import get_redis_service
from logger import logger
from service.youtube_service import YoutubeService, VideoFormat
from typing import Optional, Annotated

app = FastAPI()
settings = AppSettings()


def is_valid(pattern: str, id: str) -> bool:
    regex = re.compile(pattern)
    results = regex.match(id)
    if not results:
        return False
    return True


@app.get("/get-video-data/{video_id}")
async def get_data_from_youtube(video_id: str):
    """
        Retrieve stream URL by videoId.
        This endpoint fetches the streaming url for a specified YouTube video.
        Used YouTube API v3

        - Args:
            video_id (str): A valid YouTube video ID.
        - Returns:
            dict: A dictionary containing the information about video
        - Example:
            GET /get-download-link/dQw4w9WgXcQ
    """

    pattern = settings.youtube_video_id_pattern
    if not is_valid(pattern, video_id):
        raise HTTPException(status_code=400, detail=f"Video id don't match pattern={pattern}")
    res = await YoutubeService(video_id).get_video_data()
    if 'items' not in res or not res['items']:
        raise HTTPException(status_code=404, detail=f"Video with id {video_id} not found")
    return res['items'][0]


@app.get("/get-download-link/{video_id}")
async def get_metadata(video_id: str, redis=Depends(get_redis_service)):
    """
    Retrieve stream URL by videoId.
    This endpoint fetches the streaming url for a specified YouTube video

    - Args:
        video_id (str): A valid YouTube video ID.
    - Returns:
        url (str): The direct stream URL for downloading the video.
    - Example:
        GET /get-download-link/dQw4w9WgXcQ
    """

    cache = await redis.get_cache(key=f"{video_id}")
    if cache:
        return cache.decode()
    res = await YoutubeService(video_id).fetch_video_info()
    await redis.set_cache(key=f"{video_id}", value=res.url, expire=120)
    return res.url


@app.get("/get-download-link/{video_id}/{fmt_video}")
async def get_metadata_with_fmt(video_id: str, fmt_video: Annotated[str, VideoFormat],
                                redis=Depends(get_redis_service)):
    """
    Retrieve stream URL by videoId and format video.
    This endpoint fetches the streaming information for a specified YouTube video,
    including the duration, file size, title, download URL, and resolution based on
    the provided video ID and format.

    - Args:
        video_id (str): A valid YouTube video ID.
        fmt_video (str): Desired format for the video (e.g., 'mp4', 'mov').
    - Returns:
        dict: A dictionary containing the following information:
            - duration (float): The duration of the video in seconds.
            - filesize_mb (float): The size of the video file in megabytes.
            - title (str): The title of the video.
            - url (str): The direct stream URL for downloading the video.
            - resolution (str): The resolution of the video.
    - Example:
        GET /get-download-link/dQw4w9WgXcQ/mp4
    """

    cache = await redis.get_cache(key=f"{video_id}&{fmt_video}")
    if cache:
        return json.loads(cache.decode())

    res = await YoutubeService(video_id, fmt_video).fetch_video_info()
    result = {
        "duration": res._monostate.duration,
        "filesize_mb": res._filesize_mb,
        "title": res._monostate.title,
        "url": res.url,
        "resolution": res.resolution
    }
    await redis.set_cache(key=f"{video_id}&{fmt_video}", value=json.dumps(result), expire=120)
    return result
