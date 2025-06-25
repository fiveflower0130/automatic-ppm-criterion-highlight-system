from app.database.redis import redis_client

# 快取查詢
async def get_cache(key: str):
    value = await redis_client.get(key)
    return value

# 快取寫入
async def set_cache(key: str, value: str, ex: int = None):
    await redis_client.set(key, value, ex=ex)

# 快取刪除
async def del_cache(key: str):
    await redis_client.delete(key)

# 快取是否存在
async def exists_cache(key: str):
    exists = await redis_client.exists(key)
    return exists
