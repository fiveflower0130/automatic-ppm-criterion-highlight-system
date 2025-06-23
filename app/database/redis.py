import aioredis
from app.config import Config

# Redis 連線設定
redis_client = aioredis.from_url(
    f"redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}",
    password=Config.REDIS_PASSWORD,
    encoding="utf-8",
    decode_responses=True,
)