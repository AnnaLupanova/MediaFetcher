from fastapi import HTTPException
from typing import Optional, Annotated
from utils import BaseService
import instaloader


class InstagramService(BaseService):

    def get_stream(self):
        try:
            loader = instaloader.Instaloader()
            loader.login("test", "test")
            post = instaloader.Post.from_shortcode(loader.context, self.content_id)
            return post
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))