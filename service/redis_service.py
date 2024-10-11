import redis.asyncio as redis
from logger import logger
from settings import settings
from typing import Optional


class RedisService:
    def __init__(self, pool) -> None:
        self._redis = redis.Redis(connection_pool=pool)

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

    @classmethod
    def create_pool(cls) -> Optional[redis.connection.ConnectionPool]:
        try:
            return redis.ConnectionPool(host=settings.redis_host, port=settings.redis_port, db=0)
        except Exception as e:
            logger.error(f'Have error in create_pool(), reason <{str(e)}>')


redis_pool = RedisService.create_pool()


async def get_redis_service() -> RedisService:
    return RedisService(pool=redis_pool)
