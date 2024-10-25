import aiohttp.client_exceptions
from fastapi import HTTPException
import aiohttp
from typing import Optional, Annotated, Dict, Any
from pytubefix import Stream
from pytubefix import YouTube, exceptions
from pytubefix.cli import on_progress
import re
from enum import Enum
import asyncio
from logger import get_logger
from settings import settings
from utils import BaseService

logger = get_logger('api_logger.log')


class VideoFormat(Enum):
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"


class YoutubeService(BaseService):
    def get_stream(self) -> dict[str, Any]:
        try:
            link = f"https://www.youtube.com/watch?v={self.content_id}"
            if self.fmt and self.fmt not in (format.value for format in VideoFormat):
                raise HTTPException(status_code=400, detail=f"Unsupported format: {self.fmt}")

            res = YouTube(link, on_progress_callback=on_progress).streams.filter(subtype=self.fmt) \
                .order_by("resolution").desc().first()

            return {
                "duration": res._monostate.duration,
                "filesize_mb": res._filesize_mb,
                "title": res._monostate.title,
                "url": res.url,
                "resolution": res.resolution
            }


        except exceptions.VideoUnavailable:
            raise HTTPException(status_code=404, detail="Video not found")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f'Have error in get_stream(), reason <{str(e)}>')
            ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
            message = ansi_escape.sub('', str(e))
            raise HTTPException(status_code=400, detail=message)
