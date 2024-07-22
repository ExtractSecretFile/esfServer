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

# 配置 Redis 数据库
r = redis.StrictRedis(host="localhost", port=6379, db=0, password=redis_password)


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
    existing_code = r.get(serial_number)

    if existing_code:
        if existing_code.decode("utf-8") == registration_code:
            return {"verified": True}
        else:
            return {"verified": False}
    else:
        # 注册新的序列号
        r.set(serial_number, registration_code)
        return {"verified": True}


if __name__ == "__main__":

    uvicorn.run(app, host="0.0.0.0", port=8000)
