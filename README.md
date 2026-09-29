# Домашнее задание к лекции «Flask»

REST API для сайта объявлений на Flask + SQLAlchemy + PostgreSQL.

## Запуск

1. Поднять PostgreSQL:

```bash
docker compose --env-file .env up -d
```

2. Установить зависимости:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Запустить сервер:

```bash
python server.py
```

4. Проверить запросы (в другом терминале):

```bash
python client.py
```

## API

### Пользователи

| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/users` | Регистрация (`email`, `password`) |
| GET | `/users/<id>` | Получить пользователя |

### Объявления

| Метод | URL | Auth | Описание |
|-------|-----|------|----------|
| POST | `/advertisements` | Basic (email:password) | Создать объявление |
| GET | `/advertisements/<id>` | — | Получить объявление |
| PATCH | `/advertisements/<id>` | Basic, только владелец | Редактировать |
| DELETE | `/advertisements/<id>` | Basic, только владелец | Удалить |

Поля объявления: `title`, `description`, `created_at`, `owner`.

### Пример

```bash
# регистрация
curl -X POST http://127.0.0.1:5000/users \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret"}'

# создать объявление
curl -X POST http://127.0.0.1:5000/advertisements \
  -u user@example.com:secret \
  -H "Content-Type: application/json" \
  -d '{"title":"Продам ноутбук","description":"Отличное состояние"}'
```
