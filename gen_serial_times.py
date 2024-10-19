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

# database id
redis_multi_db = int(os.getenv("REDIS_MULTI_DB"))
redis_total_count_db = int(os.getenv("REDIS_TOTAL_COUNT_DB"))
redis_used_count_db = int(os.getenv("REDIS_USED_COUNT_DB"))

# 配置 Redis 数据库
r_multi = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_multi_db, password=redis_password
)
r_total_count = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_total_count_db, password=redis_password
)
r_used_count = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_used_count_db, password=redis_password
)


def generate_serial_number():
    uuid_ = uuid.uuid4()
    return str(uuid.uuid5(uuid_, "authkey")).replace("-", "")[:10]


def add_new_serial_numbers(count, total_count):
    for _ in range(count):
        serial_number = generate_serial_number()
        try:
            sn = r_multi.get(serial_number)
            if sn is not None:
                continue
            # 空 key 表示未注册
            r_multi.set(serial_number, "")
            r_total_count.set(serial_number, total_count)
            r_used_count.set(serial_number, 0)
        # 连接错误
        except redis.ConnectionError:
            print("连接失败！")
            break
        print(f"{serial_number}")


def main():
    try:
        num = int(sys.argv[1])
        total_count = int(sys.argv[2])
        add_new_serial_numbers(num, total_count)
    except IndexError:
        print("Usage: python generate_serial_times.py <num> <total_count>")
        sys.exit(1)
    except ValueError as e:
        print(f"Invalid argument: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
