from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import  Field

import re

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    youtube_video_id_pattern: str 
    youtube_api_key: str 
    youtube_api_url: str
    redis_host: str
    redis_port: int

