import aiohttp.client_exceptions
from fastapi import HTTPException
import aiohttp
from typing import Optional, Annotated
from concurrent.futures import ThreadPoolExecutor
import asyncio
import instaloader


class InstagramService:
    def __init__(self, reels_id: str):
        self.reels_id = reels_id

    def get_stream(self):
        loader = instaloader.Instaloader()
        loader.login("USER", "password")
        post = instaloader.Post.from_shortcode(loader.context, "CQiiyb-lE5HrPdUGrlIMAMR7aVARvq5k-0ujes0")
        return post

    async def fetch_video_info(self):
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            return await loop.run_in_executor(pool, self.get_stream)