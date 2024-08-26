import os
from typing import Optional

import redis.asyncio as redis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

REDIS_ERROR = "Failed to connect backend DB"
KEY_NOT_EXISTING = "Invalid Registeration code!"

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
    error: Optional[str]


class ValidateRequest(BaseModel):
    serial_number: str


class ValidateResponse(BaseModel):
    used: bool
    error: Optional[str]
    regkey: Optional[str]


class ReverseRequest(BaseModel):
    registeration_code: str


class ReverseResponse(BaseModel):
    serial_number: Optional[str]
    error: Optional[str]


@app.post("/reverse", response_model=ReverseResponse)
async def reverse(data: ReverseRequest):
    target_regcode = data.registeration_code
    sn = None
    try:
        async for key in r.scan_iter(count=16384):
            regcode = (await r.get(key)).decode("utf-8")
            if regcode == target_regcode:
                sn = key.decode("utf-8")
                break
    except redis.ConnectionError:
        # don't drop the incomplete result
        return {"error": REDIS_ERROR, "serial_number": sn}

    return {"error": None, "serial_number": sn}


@app.post("/validate", response_model=ValidateResponse)
async def validate(data: ValidateRequest):
    sn = data.serial_number

    try:
        existing_code = await r.get(sn)
    except redis.ConnectionError:
        return {"error": REDIS_ERROR, "used": False}

    re = {"error": None, "used": bool(existing_code), "regkey": None}

    if existing_code is None:  # not existing
        re["error"] = KEY_NOT_EXISTING
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
        existing_code = await r.get(serial_number)
    except redis.ConnectionError:
        return {"error": REDIS_ERROR, "verified": False}

    # 不存在
    if existing_code is None:
        return {"verified": False, "error": KEY_NOT_EXISTING}

    # 存在且非空
    if existing_code:
        if existing_code.decode("utf-8") == registration_code:
            return {"verified": True, "error": None}
        else:
            return {"verified": False, "error": "Already registered"}
    else:
        # 注册新的序列号
        try:
            await r.set(serial_number, registration_code)
        except redis.ConnectionError:
            return {"error": REDIS_ERROR, "verified": False}
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
