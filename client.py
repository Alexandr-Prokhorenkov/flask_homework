import requests

BASE_URL = "http://127.0.0.1:5000"

# --- регистрация пользователя ---
response = requests.post(
    f"{BASE_URL}/users",
    json={"email": "owner@example.com", "password": "1234"},
)
print("CREATE USER:", response.status_code, response.json())

# --- создание объявления (только авторизованный пользователь) ---
response = requests.post(
    f"{BASE_URL}/advertisements",
    json={"title": "Продам велосипед", "description": "Почти новый"},
    auth=("owner@example.com", "1234"),
)
print("CREATE AD:", response.status_code, response.json())
ad_id = response.json().get("id")

# --- получение объявления ---
response = requests.get(f"{BASE_URL}/advertisements/{ad_id}")
print("GET AD:", response.status_code, response.json())

# --- редактирование объявления (только владелец) ---
response = requests.patch(
    f"{BASE_URL}/advertisements/{ad_id}",
    json={"title": "Продам велосипед срочно"},
    auth=("owner@example.com", "1234"),
)
print("PATCH AD:", response.status_code, response.json())

# --- удаление объявления (только владелец) ---
response = requests.delete(
    f"{BASE_URL}/advertisements/{ad_id}",
    auth=("owner@example.com", "1234"),
)
print("DELETE AD:", response.status_code, response.json())
