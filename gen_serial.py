import os
import sys
import uuid

import redis
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 从环境变量中获取 Redis 密码
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_db = int(os.getenv("REDIS_DB"))

# 配置 Redis 数据库
r = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_db, password=redis_password
)


def generate_serial_number():
    uuid_ = uuid.uuid4()
    return str(uuid.uuid5(uuid_, "authkey"))


def add_new_serial_numbers(count_):
    for _ in range(count_):
        serial_number = generate_serial_number()
        try:
            # 空 key 表示未注册
            r.set(serial_number, "")
        # 连接错误
        except redis.ConnectionError:
            print("连接失败！")
            break
        print(f"{serial_number}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python generate_serials.py <count>")
        sys.exit(1)

    count = int(sys.argv[1])
    add_new_serial_numbers(count)


if __name__ == "__main__":
    main()
