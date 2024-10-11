import aiohttp.client_exceptions
from fastapi import HTTPException
import aiohttp
from typing import Optional, Annotated
from pytubefix import Stream
from concurrent.futures import ThreadPoolExecutor
from pytubefix import YouTube, exceptions
from pytubefix.cli import on_progress
import re
from enum import Enum
import asyncio
from logger import logger
from settings import settings
from logger import logger

class VideoFormat(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"

class YoutubeService:
    def __init__(self, video_id: str, fmt: Annotated[str, VideoFormat] = VideoFormat.MP4.value):
        self.video_id = video_id
        self.fmt = fmt

    async def get_video_data(self) -> Optional[dict]:
        params = {
            "part": "snippet",
            "id": self.video_id,
            "key": settings.youtube_api_key
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(settings.youtube_api_url, params=params, ssl=False) as response:
                    result = await response.json()
                    if response.status != 200:
                        raise HTTPException(status_code=response.status, detail=result["error"]["message"])
                    return result
        except aiohttp.client_exceptions.ClientError:
            raise HTTPException(status_code=503, detail="Service youtube unavailable")
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    def get_stream(self) -> Optional[Stream]:
        try:
            link = f"https://www.youtube.com/watch?v={self.video_id}"
            if self.fmt and self.fmt not in (format.value for format in VideoFormat):
                print()
                raise HTTPException(status_code=400, detail=f"Unsupported format: {self.fmt}")

            return YouTube(link, on_progress_callback=on_progress).streams.filter(subtype=self.fmt) \
                .order_by("resolution").desc().first()

        except exceptions.VideoUnavailable:
            raise HTTPException(status_code=404, detail="Video not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Have error in get_stream(), reason <{str(e)}>')
            ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
            message = ansi_escape.sub('', str(e))
            raise HTTPException(status_code=400, detail=message)

    async def fetch_video_info(self) -> Optional[Stream]:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_stream)
