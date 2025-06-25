import json
from app.database.redis import redis_client

async def get_cache(key: str):
    value = await redis_client.get(key)
    return json.loads(value) if value else None

async def set_cache(key: str, value, ex: int = None):
    value = json.dumps(value)
    if ex:
        await redis_client.set(key, value, ex=ex)
    else:
        await redis_client.set(key, value)

async def exists_cache(key: str):
    return await redis_client.exists(key)

async def delete_cache(key: str):
    await redis_client.delete(key)

# class RedisHelper:
#     def __init__(self, redis_client):
#         self._redis = redis_client

#     async def get(self, key: str):
#         value = await self._redis.get(key)
#         return json.loads(value) if value else None

#     async def set(self, key: str, value, ex: int = None):
#         value = json.dumps(value)
#         if ex:
#             await self._redis.set(key, value, ex=ex)
#         else:
#             await self._redis.set(key, value)

#     async def exists(self, key: str):
#         return await self._redis.exists(key)

#     async def delete(self, key: str):
#         await self._redis.delete(key)