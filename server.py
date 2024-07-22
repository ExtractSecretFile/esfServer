import os

import redis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

# 加载 .env 文件
load_dotenv()

app = FastAPI()

# 从环境变量中获取 Redis 密码
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))
redis_db = int(os.getenv("REDIS_DB"))

# 配置 Redis 数据库
r = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_db, password=redis_password
)


# 请求体模型
class RegistrationRequest(BaseModel):
    serial_number: str
    registration_code: str


class RegistrationResponse(BaseModel):
    verified: bool


@app.post("/register", response_model=RegistrationResponse)
async def register(data: RegistrationRequest):
    serial_number = data.serial_number
    registration_code = data.registration_code

    # 检查序列号是否已经注册
    try:
        existing_code = r.get(serial_number)
    except redis.ConnectionError:
        return {"error": "Failed to connect backend DB", "verified": False}

    if existing_code:
        if existing_code.decode("utf-8") == registration_code:
            return {"verified": True}
        else:
            return {"verified": False}
    else:
        # 注册新的序列号
        try:
            r.set(serial_number, registration_code)
        except redis.ConnectionError:
            return {"error": "Failed to connect backend DB", "verified": False}
        return {"verified": True}


if __name__ == "__main__":
    api_port = os.getenv("API_PORT")
    uvicorn.run(app, host="0.0.0.0", port=api_port)
