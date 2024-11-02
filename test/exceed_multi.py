import sys
import asyncio
import random
from string import digits, ascii_lowercase

import aiohttp


async def main():
    alphanum = digits + ascii_lowercase
    rand = random.Random()
    times = int(sys.argv[1])
    sn = sys.argv[2]

    keys = ["".join(rand.choices(alphanum, k=9)) for _ in range(times + 1)]

    async def proc_single(key: str):
        async with session.post(
            "http://8.134.130.103:8000/register",
            json={
                "serial_number": sn,
                "registration_code": key,
            },
        ) as result:
            print(await result.text())

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*(proc_single(key) for key in keys))


if __name__ == "__main__":
    asyncio.run(main())
