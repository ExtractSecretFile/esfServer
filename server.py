import os
from datetime import datetime
from typing import Optional

import redis.asyncio as redis
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
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
redis_lookup_db = int(os.getenv("REDIS_LOOKUP_DB"))
redis_time_db = int(os.getenv("REDIS_TIME_DB"))
redis_ip_db = int(os.getenv("REDIS_IP_DB"))

# 配置 Redis 数据库
r = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_db, password=redis_password
)
r_lookup = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_lookup_db, password=redis_password
)
r_time = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_time_db, password=redis_password
)
r_ip = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_ip_db, password=redis_password
)


class RegistrationResponse(BaseModel):
    verified: bool
    error: Optional[str]


class ValidateRequest(BaseModel):
    serial_number: str


class ValidateResponse(BaseModel):
    error: Optional[str]
    used: bool
    regkey: Optional[str]
    regtime: Optional[str]
    source_ip: Optional[str]


class ReverseRequest(BaseModel):
    registeration_code: str


class ReverseResponse(BaseModel):
    error: Optional[str]
    serial_number: Optional[str]
    register_time: Optional[str]
    source_ip: Optional[str]


@app.post("/reverse", response_model=ReverseResponse)
async def reverse(data: ReverseRequest):
    regcode = data.registeration_code
    try:
        sn = await r_lookup.get(regcode)
        reg_time = await r_time.get(sn)
        source_ip = await r_ip.get(sn)
    except redis.ConnectionError:
        return {
            "error": REDIS_ERROR,
            "serial_number": None,
            "register_time": None,
            "source_ip": None,
        }

    return {
        "error": None,
        "serial_number": sn,
        "register_time": reg_time,
        "source_ip": source_ip,
    }


@app.post("/validate", response_model=ValidateResponse)
async def validate(data: ValidateRequest):
    sn = data.serial_number

    result = {
        "error": None,
        "used": None,
        "regkey": None,
        "regtime": None,
        "source_ip": None,
    }

    try:
        existing_code = await r.get(sn)
    except redis.ConnectionError:
        result["error"] = REDIS_ERROR
        return result

    if existing_code is None:  # not existing
        result["error"] = KEY_NOT_EXISTING
        result["used"] = False
    else:
        result["regkey"] = existing_code.decode("utf-8")
        result["used"] = True

    try:
        result["regtime"] = await r_time.get(sn)
        result["source_ip"] = await r_ip.get(sn)
    except redis.ConnectionError:
        result["error"] = REDIS_ERROR
        return result

    return result


@app.post("/register", response_model=RegistrationResponse)
async def register(request: Request):
    data = await request.json()

    source_ip = request.client.host
    serial_number = data["serial_number"]
    registration_code = data["registration_code"]

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
            print(registration_code, serial_number)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await r_time.set(serial_number, now)
            await r_lookup.set(registration_code, serial_number)
            await r_ip.set(serial_number, source_ip)
        except redis.ConnectionError:
            return {"error": REDIS_ERROR, "verified": False}
        return {"verified": True, "error": None}


def main():
    """
    verify api
    """
    api_port = int(os.getenv("API_PORT"))
    uvicorn.run(
        app,
        # public
        host="0.0.0.0",
        port=api_port,
    )


if __name__ == "__main__":
    main()
