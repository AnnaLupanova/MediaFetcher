import os

import redis.asyncio as redis
from logger import get_logger
from settings import settings
from typing import Optional


logger = get_logger('api_logger.log')

class RedisService:
    def __init__(self) -> None:
        self._redis = redis.from_url(settings.redis_url, db=0)

    async def set_cache(self, key, value, expire) -> None:
        try:
            await self._redis.set(name=key, value=value, ex=expire)
        except Exception as e:
            logger.error(f'Have error in set_cache(), reason <{str(e)}>')

    async def get_cache(self, key) -> bytes:
        try:
            return await self._redis.get(name=key)
        except Exception as e:
            logger.error(f'Have error in get_cache(), reason <{str(e)}>')


redis_pool = RedisService()

async def get_redis_service() -> RedisService:
    return redis_pool
