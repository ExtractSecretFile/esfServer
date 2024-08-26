import os
from typing import Optional

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
    error: Optional[str]
    verified: bool


class ValidateRequest(BaseModel):
    serial_number: str


class ValidateResponse(BaseModel):
    used: bool
    error: Optional[str]
    regkey: Optional[str]


@app.post("/validate", response_model=ValidateResponse)
async def validate(data: ValidateRequest):
    sn = data.serial_number

    try:
        existing_code = r.get(sn)
    except redis.ConnectionError:
        return {"error": "Failed to connect backend DB", "used": False}

    re = {"error": None, "used": bool(existing_code), "regkey": None}

    if existing_code is None:  # not existing
        re["error"] = "Invalid Registeration code!"
    else:
        re["regkey"] = existing_code.decode("utf-8")

    return re


@app.post("/register", response_model=RegistrationResponse)
async def register(data: RegistrationRequest):
    serial_number = data.serial_number
    registration_code = data.registration_code

    print(serial_number)
    # 检查序列号是否已经注册
    try:
        existing_code = r.get(serial_number)
    except redis.ConnectionError:
        return {"error": "Failed to connect backend DB", "verified": False}

    # 不存在
    if existing_code is None:
        return {"verified": False, "error": "Invalid Registeration code!"}

    # 存在且非空
    if existing_code:
        if existing_code.decode("utf-8") == registration_code:
            return {"verified": True, "error": None}
        else:
            return {"verified": False, "error": "Already registered"}
    else:
        # 注册新的序列号
        try:
            r.set(serial_number, registration_code)
        except redis.ConnectionError:
            return {"error": "Failed to connect backend DB", "verified": False}
        return {"verified": True, "error": None}


def main():
    """
    verify api
    """
    api_port = os.getenv("API_PORT")
    uvicorn.run(
        app,
        # public
        host="0.0.0.0",
        port=api_port,
    )


if __name__ == "__main__":
    main()
