import os

import redis.asyncio as redis
from dotenv import load_dotenv

REDIS_ERROR = "Failed to connect backend DB"
KEY_NOT_EXISTING = "Invalid Registeration code!"

# 加载 .env 文件
load_dotenv()

# 从环境变量中获取 Redis 密码
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_db = int(os.getenv("REDIS_DB"))
redis_lookup_db = int(os.getenv("REDIS_LOOKUP_DB"))

# 配置 Redis 数据库
r = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_db, password=redis_password
)
r_lookup = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_lookup_db, password=redis_password
)


async def main():
    keys = await r.keys()
    for key in keys:
        v = await r.get(key)
        v = v.decode("utf-8")

        # not used
        if not v:
            continue

        await r_lookup.set(v, key)


if __name__ == "__main__":
    main()
