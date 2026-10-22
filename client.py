import asyncio

import aiohttp

BASE_URL = "http://127.0.0.1:8080"
AUTH = aiohttp.BasicAuth("owner@example.com", "1234")


async def main():
    async with aiohttp.ClientSession() as session:
        # --- регистрация пользователя ---
        async with session.post(
            f"{BASE_URL}/users",
            json={"email": "owner@example.com", "password": "1234"},
        ) as resp:
            print("CREATE USER:", resp.status, await resp.json())

        # --- создание объявления (только авторизованный пользователь) ---
        async with session.post(
            f"{BASE_URL}/advertisements",
            json={"title": "Продам велосипед", "description": "Почти новый"},
            auth=AUTH,
        ) as resp:
            data = await resp.json()
            print("CREATE AD:", resp.status, data)
            ad_id = data.get("id")

        # --- получение объявления ---
        async with session.get(f"{BASE_URL}/advertisements/{ad_id}") as resp:
            print("GET AD:", resp.status, await resp.json())

        # --- редактирование объявления (только владелец) ---
        async with session.patch(
            f"{BASE_URL}/advertisements/{ad_id}",
            json={"title": "Продам велосипед срочно"},
            auth=AUTH,
        ) as resp:
            print("PATCH AD:", resp.status, await resp.json())

        # --- удаление объявления (только владелец) ---
        async with session.delete(
            f"{BASE_URL}/advertisements/{ad_id}",
            auth=AUTH,
        ) as resp:
            print("DELETE AD:", resp.status, await resp.json())


asyncio.run(main())
