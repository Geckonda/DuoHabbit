# 🦊 Duohabit

<!-- [![CI Status](https://github.com/your-org/duohabit/actions/workflows/ci.yml/badge.svg)](https://github.com/Geckonda/duohabit/actions/workflows/ci.yml) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/Vue-3-42b883.svg)](https://vuejs.org/)

**Строим привычки вместе!**

---

## 📋 О проекте

Duohabit — платформа для формирования привычек. Замысел в том, чтобы успех зависел от каждого участника команды: общий стрик, общая ответственность, нельзя подвести своих.

### Что работает сейчас

- регистрация и вход по email с токеном в БД;
- персональные привычки: создание, редактирование, архивация и восстановление;
- отметка выполнения за день (одна отметка на привычку в день);
- подсчёт текущего стрика по собственным отметкам;
- приватные и публичные привычки (флаг `is_private`).

### Что задумано, но ещё не реализовано

- команды по 2-5 человек и общий стрик на группу;
- сброс стрика у всех, если кто-то пропустил день;
- учёт часовых поясов участников.

Групп и команд в коде пока нет: привычка принадлежит одному пользователю, стрик считается по его собственным отметкам.

---

## 🏗 Архитектура

```
Frontend (Vue 3 + Vite)  ←→  Backend (FastAPI)  ←→  PostgreSQL
                                    ↕
                                  Redis
```

### Технологический стек

| Компонент | Технология |
|-----------|------------|
| Язык бэкенда | Python 3.13, пакеты через `uv` |
| Backend | FastAPI + uvicorn |
| Аутентификация | fastapi-users, Bearer-токены в БД |
| ORM | SQLAlchemy 2 (async) + asyncpg |
| Database | PostgreSQL 17 |
| Cache | Redis 8 (поднят, в коде пока не используется) |
| Конфигурация | pydantic-settings |
| Frontend | Vue 3 + Pinia + vue-router + axios |
| Сборка фронта | Vite 7, пакеты через `pnpm` |
| Окружение | Docker + Dev Containers, pgAdmin |
| Качество кода | isort, black, mypy, pylint |

---

## 🚀 Быстрый старт

Проект разрабатывается в dev-контейнере: PostgreSQL, Redis и pgAdmin поднимаются docker compose, а само приложение запускается внутри контейнера разработчика.

### Предварительные требования

- [Docker](https://www.docker.com/products/docker-desktop) и Docker Compose
- [VS Code](https://code.visualstudio.com/) или Cursor с расширением **Dev Containers**
- [Git](https://git-scm.com/)

### Шаги

```bash
# 1. Клонируем репозиторий
git clone https://github.com/Geckonda/duohabit.git
cd duohabit

# 2. Генерируем .env и .devcontainer/.env (запускать строго из корня репозитория)
python backend/duohabit/scripts/generate_env.py
```

3. Открываем папку в VS Code и выполняем команду **Dev Containers: Reopen in Container**.

4. Дальше — внутри контейнера:

```bash
# Бэкенд
task backend_install
task backend_up          # http://localhost:8000/docs

# Фронтенд (в отдельном терминале)
cd frontend
pnpm install
pnpm run dev --host      # http://localhost:5173
```

> ⚠️ Задачи `task frontend_install` / `task frontend_up` / `task frontend_quality` сейчас указывают на каталог `frontend/duohabit`, которого нет — код фронта лежит в `frontend/`. До исправления Taskfile запускайте фронт командами выше.

### Что где открывается

| Сервис | Адрес | Доступ |
|--------|-------|--------|
| Backend API | http://localhost:8000 | — |
| Swagger UI | http://localhost:8000/docs | — |
| Frontend | http://localhost:5173 | — |
| pgAdmin | http://localhost:5050 | `admin@admin.com` / `admin` |

Порты бэкенда и фронта пробрасывает VS Code. Чтобы они не менялись при ручных перезапусках, закрепите их в панели **Ports** — обе команды поддерживают hot reload и переживают такое закрепление.

При первом старте приложение создаёт администратора: **`admin@duohabit.com` / `admin`**. Смените пароль перед тем, как выкладывать проект наружу.

Подробности процесса разработки — в [how_develop.md](how_develop.md).

---

## 🔐 Переменные окружения

Логические переменные живут в [fillme.env](fillme.env). Скрипт [generate_env.py](backend/duohabit/scripts/generate_env.py) разворачивает их в два файла и дописывает недостающие секреты:

```
fillme.env  ──generate_env.py──┬──> .env                (для деплоя)
                               └──> .devcontainer/.env  (читает docker compose)
```

Скрипт добавляет только недостающие поля и прерывается, если поле уже есть, но с другим значением.

На практике это значит, что запускать его нужно **один раз на свежем клоне**. Повторный запуск на готовом окружении всегда завершится ошибкой вида:

```
Error: Field 'REDIS_PASSWORD' exists in .env with a different value
Aborting to prevent conflicts.
```

Так и задумано: `REDIS_PASSWORD`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` и `JWT_SECRET` объявлены в `fillme.env` пустыми, а в `.env` уже лежат сгенерированные значения. Файлы при этом не меняются. Новые переменные и правки секретов вносите в `.env` и `.devcontainer/.env` руками.

| Переменная | Назначение |
|------------|------------|
| `LOG_LEVEL` | Уровень логирования, по умолчанию `INFO` |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Адрес базы (`postgres:5432` внутри compose-сети) |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Креды PostgreSQL, генерируются автоматически |
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | Подключение к Redis |
| `JWT_SECRET` | Секрет приложения, генерируется автоматически |
| `VITE_API_URL` | Базовый URL API для фронта, по умолчанию `http://localhost:8000` |

Два момента, о которые легко споткнуться:

- `Settings` в [config.py](backend/duohabit/config.py) читает **переменные окружения процесса**, а не `.env`-файл. В dev-контейнере их передаёт docker compose через `env_file`; при ручном запуске вне контейнера переменные нужно экспортировать самому.
- Если перегенерировать секреты после того, как том с данными PostgreSQL уже создан, пароль в базе и в `.env` разойдутся. Том нужно удалить:

```bash
docker compose -f .devcontainer/docker-compose.dev.yml down -v
```

---

## 📁 Структура проекта

```
duohabit/
├── .devcontainer/              # Dev-контейнер: postgres, redis, pgadmin
├── docs/                       # Документация и ТЗ
├── infrastructure/             # Инфраструктурные конфиги (пока пусто)
├── backend/
│   ├── duohabit/
│   │   ├── main.py             # Точка входа, создание приложения
│   │   ├── config.py           # Настройки из окружения
│   │   ├── db.py               # Engine, sessionmaker, Base
│   │   ├── auth.py             # fastapi-users: бэкенд аутентификации, зависимости
│   │   ├── routers/            # HTTP-эндпоинты
│   │   ├── services/           # Бизнес-логика
│   │   ├── repositories/       # Работа с данными
│   │   ├── models/             # SQLAlchemy-модели
│   │   ├── schemas/            # Pydantic-схемы
│   │   ├── utils/              # Хелперы
│   │   └── scripts/            # generate_env, danger_dropdb
│   ├── pyproject.toml
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── api/                # axios-клиент и вызовы API
│   │   ├── views/              # Страницы
│   │   ├── components/         # Компоненты
│   │   ├── stores/             # Pinia-сторы
│   │   ├── router/             # vue-router
│   │   └── types/
│   ├── package.json
│   └── vite.config.js
├── Taskfile.yml
├── fillme.env
└── how_develop.md
```

### Слои бэкенда

- **routers** — маршруты и зависимости, никакой бизнес-логики;
- **services** — бизнес-логика, здесь же выполняется `commit`;
- **repositories** — запросы к БД, коммитов не делают.

---

## 🔌 API

Полное описание — в Swagger UI: http://localhost:8000/docs

Аутентификация — Bearer-токен: `Authorization: Bearer <access_token>`.

### Auth

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/auth/login` | Вход. Форма `form-data`, поле `username` — это email |
| `POST` | `/auth/logout` | Выход, токен инвалидируется |

### Users

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/users/` | Регистрация. Права админа может выдать только админ |
| `GET` | `/users/` | Список пользователей, параметры `offset` и `limit` (1-100, по умолчанию 10) |
| `GET` | `/users/me` | Текущий пользователь |
| `GET` | `/users/{user_id}` | Пользователь по id |

### Habits

| Метод | Путь | Описание |
|-------|------|----------|
| `POST` | `/habits` | Создать привычку |
| `GET` | `/habits` | Свои привычки |
| `GET` | `/habits/{habit_id}` | Одна привычка |
| `GET` | `/habits/{habit_id}/details` | Привычка вместе с отметками |
| `PATCH` | `/habits/{habit_id}` | Изменить привычку |
| `DELETE` | `/habits/{habit_id}` | Удалить привычку |
| `POST` | `/habits/{habit_id}/archive` | В архив |
| `POST` | `/habits/{habit_id}/restore` | Вернуть из архива |
| `POST` | `/habits/{habit_id}/check` | Отметить выполнение, в ответе новый стрик |
| `GET` | `/habits/{habit_id}/checks` | Отметки по привычке |
| `DELETE` | `/habits/checks/{check_id}` | Удалить отметку |

---

## 📊 Модели данных

Идентификаторы — целочисленные, у всех сущностей есть `created_at` и `updated_at`.

### User

| Поле | Тип | Примечание |
|------|-----|------------|
| `id` | `int` | |
| `email` | `str` | Уникальный, он же логин |
| `username` | `str` | |
| `sex` | `int?` | Необязательное |
| `is_platform_admin` | `bool` | Права администратора платформы |
| `is_active`, `is_superuser`, `is_verified` | `bool` | Поля fastapi-users |

### Habit

| Поле | Тип | Примечание |
|------|-----|------------|
| `id` | `int` | |
| `user_id` | `int` | Владелец, каскадное удаление |
| `title` | `str` | До 200 символов |
| `description` | `str?` | До 500 символов |
| `habit_type` | `str` | `daily`, `weekdays`, `weekly`, `monthly` |
| `current_streak` | `int` | Пересчитывается при отметке и при удалении отметки |
| `is_active` | `bool` | `false` — привычка в архиве |
| `is_private` | `bool` | По умолчанию `true` |

### HabitCheck

| Поле | Тип | Примечание |
|------|-----|------------|
| `id` | `int` | |
| `habit_id` | `int` | Каскадное удаление вместе с привычкой |
| `check_date` | `date` | Пара `(habit_id, check_date)` уникальна |

### AccessToken

Таблица токенов fastapi-users. Время жизни сессии — 30 дней (`session_lifetime` в [config.py](backend/duohabit/config.py)).

---

## 🧪 Разработка

### Качество кода

```bash
task backend_quality     # isort, black, mypy, pylint
```

Pylint держим полностью довольным, mypy — в разумных пределах.

### Тесты

```bash
task backend_test        # uv run pytest -v
```

⚠️ Каталога `tests/` в репозитории пока нет — задача заготовлена на будущее. Правила тестирования (happy path и ошибки для каждого сервиса, `@pytest.mark.asyncio(loop_scope="session")`) описаны в [how_develop.md](how_develop.md).

### Сброс базы

Только для локальной разработки:

```bash
cd backend
uv run python -m duohabit.scripts.danger_dropdb --yes-i-am-sure
```

---

## 🔄 Git Flow

### Ветки

- `main` — стабильная версия, только для релизов
- `develop` — основная ветка разработки
- `feature/*` — новые фичи (например, `feature/habit-invite`)
- `bugfix/*` — исправления багов
- `release/*` — подготовка релиза

### Процесс работы

```bash
git checkout -b feature/your-feature
git add .
git commit -m "feat: краткое описание"
git push origin feature/your-feature
```

### Conventional Commits

- `feat:` — новая функциональность
- `fix:` — исправление бага
- `docs:` — изменения в документации
- `refactor:` — рефакторинг
- `test:` — добавление тестов

---

## ⚠️ Текущие ограничения

Честный список того, что стоит знать перед работой с проектом:

- **Миграций нет.** Схема создаётся при старте через `Base.metadata.create_all`. Изменение моделей на существующей базе придётся применять руками.
- **Групповой механики нет.** Привычки персональные, стрик считается по отметкам владельца.
- **Redis не используется в коде**, но переменные `REDIS_*` обязательны — без них приложение не стартует.
- **CORS открыт на `*`.** Перед публикацией список источников нужно сузить до реальных доменов.
- **`docker-compose.prod.yml` устарел и не запускается**: в нём нет сервиса `redis` (без него падает конфигурация), образ на Python 3.11 при требовании 3.13, а порт API 8005 не совпадает с 8000, на который настроен фронт. Деплой — WIP.

---

**Сделано с ❤️ для тех, кто хочет менять привычки вместе**
