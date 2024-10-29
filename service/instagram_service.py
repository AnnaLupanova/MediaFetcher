from fastapi import HTTPException
from typing import Optional, Annotated
from utils import BaseService
import instaloader
from settings import settings

class InstagramService(BaseService):

    def get_stream(self):
        try:
            loader = instaloader.Instaloader()
            loader.login(settings.instagram_user, settings.instagram_password)
            post = instaloader.Post.from_shortcode(loader.context, self.content_id)
            return post
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))