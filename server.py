import os
from datetime import datetime
from typing import Optional

import uvicorn
import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from pydantic import BaseModel

REDIS_ERROR = "Failed to connect backend DB"
KEY_NOT_EXISTING = "Invalid Registeration code!"
KEY_TIMES_USED = "Times-key used too times!"

# 加载 .env 文件
load_dotenv()

app = FastAPI()

# 从环境变量中获取 Redis 密码
redis_password = os.getenv("REDIS_PASSWORD")
redis_host = os.getenv("REDIS_HOST")
redis_port = int(os.getenv("REDIS_PORT"))

# database id
redis_db = int(os.getenv("REDIS_DB"))
redis_lookup_db = int(os.getenv("REDIS_LOOKUP_DB"))
redis_time_db = int(os.getenv("REDIS_TIME_DB"))
redis_ip_db = int(os.getenv("REDIS_IP_DB"))
redis_multi_db = int(os.getenv("REDIS_MULTI_DB"))
redis_total_count_db = int(os.getenv("REDIS_TOTAL_COUNT_DB"))
redis_used_count_db = int(os.getenv("REDIS_USED_COUNT_DB"))

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
r_multi = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_multi_db, password=redis_password
)
r_total_count = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_total_count_db, password=redis_password
)
r_used_count = redis.StrictRedis(
    host=redis_host, port=redis_port, db=redis_used_count_db, password=redis_password
)


class RegistrationResponse(BaseModel):
    verified: bool
    error: Optional[str]


class ValidateRequest(BaseModel):
    serial_number: str


class ValidateResponse(BaseModel):
    error: Optional[str]
    used: bool

    regkey: list[str]
    regtime: list[str]
    source_ip: list[str]


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

    if len(sn) == 10:
        return await validate_multi(sn)
    else:
        return await validate_single(sn)


async def validate_multi(sn: str):
    regkeys = []
    regtime = []
    source_ip = []

    result = {
        "error": None,
        "used": False,
        "regkey": regkeys,
        "regtime": regtime,
        "source_ip": source_ip,
    }

    try:
        current_auth: bytes = await r_multi.get(sn)
    except redis.ConnectionError:
        result["error"] = REDIS_ERROR
        return result

    if current_auth is None:
        result["error"] = KEY_NOT_EXISTING
        return result
    current_auth: str = current_auth.decode("utf-8")

    if current_auth == "":
        return result

    result["used"] = True
    current_auth: list[str] = current_auth.split(",")

    for reg_id in current_auth:
        time = await r_time.get(reg_id)
        ip = await r_ip.get(reg_id)

        regkeys.append(reg_id)
        regtime.append(time)
        source_ip.append(ip)

    return result


async def validate_single(sn: str):
    result = {
        "error": None,
        "used": False,
        "regkey": [],
        "regtime": [],
        "source_ip": [],
    }

    try:
        existing_code = await r.get(sn)
        result["regtime"] = [await r_time.get(sn)]
        result["source_ip"] = [await r_ip.get(sn)]
    except redis.ConnectionError:
        result["error"] = REDIS_ERROR
        return result

    if existing_code is None:  # not existing
        result["error"] = KEY_NOT_EXISTING
        result["used"] = False
    else:
        existing_code = existing_code.decode("utf-8")
        result["used"] = existing_code != ""
        result["regkey"] = [existing_code]

    return result


@app.post("/register", response_model=RegistrationResponse)
async def register(request: Request):
    data = await request.json()

    serial_number = data["serial_number"]
    registration_code = data["registration_code"]
    source_ip = request.client.host

    if len(serial_number) == 10:
        result = await verify_multi(serial_number, registration_code, source_ip)
        return result
    else:
        result = await verify_single(serial_number, registration_code, source_ip)
        return result


async def verify_multi(serial_number, registration_code, source_ip):
    try:
        current_auth: bytes = await r_multi.get(serial_number)
        used_count: bytes = await r_used_count.get(serial_number)
        total_count: bytes = await r_total_count.get(serial_number)
    except redis.ConnectionError:
        return {"error": REDIS_ERROR, "verified": False}

    if current_auth is None or used_count is None or total_count is None:
        return {
            "error": KEY_NOT_EXISTING,
            "verified": False,
        }

    current_auth: str = current_auth.decode("utf-8")
    current_auth: list = current_auth.split(",") if current_auth else []
    if registration_code in current_auth:
        return {
            "error": None,
            "verified": True,
        }

    used_count = int(used_count.decode("utf-8"))
    total_count = int(total_count.decode("utf-8"))

    try:
        current_auth.append(registration_code)

        used_count += 1
        if used_count <= total_count:
            await r_used_count.set(serial_number, used_count)
            await r_multi.set(serial_number, ",".join(current_auth))

            await r_ip.set(registration_code, source_ip)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await r_time.set(registration_code, now)

            # multi 激活的反查
            # await r_lookup.set(registration_code, serial_number)

            return {
                "error": None,
                "verified": True,
            }
        else:
            return {
                "error": KEY_TIMES_USED,
                "verified": False,
            }
    except redis.ConnectionError:
        return {"error": REDIS_ERROR, "verified": False}


async def verify_single(serial_number, registration_code, source_ip):
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
