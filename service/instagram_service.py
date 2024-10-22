from fastapi import HTTPException
from typing import Optional, Annotated
from utils import BaseService
import asyncio
import instaloader


class InstagramService(BaseService):
    def __init__(self, reels_id: str):
        super().__init__(reels_id)
        self.reels_id = reels_id

    def get_stream(self):
        try:
            loader = instaloader.Instaloader()
            loader.login("test", "test")
            post = instaloader.Post.from_shortcode(loader.context, self.reels_id)
            return post
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))