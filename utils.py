from models.token import TokenPayload
import jwt
from settings import settings
from auth import ALGORITHM, pwd_context
from fastapi import Depends, HTTPException,status
from datetime import datetime
from pydantic import ValidationError
from auth import oauth_scheme
from models.user import User
from database import fake_users_db
import re
from enum import Enum
from service.instagram_service import InstagramService
from service.youtube_service import YoutubeService

def is_valid(pattern: str, id: str) -> bool:
    regex = re.compile(pattern)
    results = regex.match(id)
    if not results:
        return False
    return True


class Source(Enum):
    youtube = "youtube", YoutubeService
    instagram = "instagram", InstagramService

    def __init__(self, value, source_class):
        self._value_ = value
        self.source_class = source_class



