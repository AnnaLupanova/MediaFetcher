from typing import Optional, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import abc
import re


class BaseService(abc.ABC):
    def __init__(self, content_id: str):
        self.content_id = content_id

    @abc.abstractmethod
    def get_stream(self) -> Any:
        ...

    async def fetch_video_info(self) -> Any:
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_stream)




def is_valid(pattern: str, id: str) -> bool:
    regex = re.compile(pattern)
    results = regex.match(id)
    if not results:
        return False
    return True
