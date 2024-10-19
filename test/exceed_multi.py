import random
from string import digits, ascii_lowercase

import requests

TIMES = 100


def main():
    alphanum = digits + ascii_lowercase
    rand = random.Random()

    for _ in range(TIMES + 1):
        key = "".join(rand.choices(alphanum, k=9))
        result = requests.post(
            "http://127.0.0.1:8000/register",
            json={
                "serial_number": "bdcbf46e1b",
                "registration_code": key,
            },
        )
        print(result.text)


if __name__ == "__main__":
    main()
