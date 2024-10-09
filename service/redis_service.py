import redis.asyncio as redis
import main

class RedisService:
    def __init__(self, pool) -> None:
        self._redis = redis.Redis(connection_pool=pool)

    async def set_cache(self, key, value, expire) -> None:
        await self._redis.set(name=key, value=value, ex=expire)

    async def get_cache(self, key):
        return await self._redis.get(name=key)

    @classmethod
    def create_pool(cls):
        return redis.ConnectionPool(host='localhost', port=6379, db=0)
        #return redis.ConnectionPool.from_url(f"redis://{main.settings.redis_host}:{main.settings.redis_port}")
