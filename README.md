# 🦊 Duohabit

<!-- [![CI Status](https://github.com/your-org/duohabit/actions/workflows/ci.yml/badge.svg)](https://github.com/Geckonda/duohabit/actions/workflows/ci.yml) -->
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

**Cooperative Habit Tracking Platform** — Строим привычки вместе! 
---

## 📋 О проекте

Duohabit — это веб-платформа для совместного формирования привычек, где успех зависит от каждого участника. Главная особенность — **общая ответственность за стрик**: если один пропустил день, стрик сбрасывается у всех.

### 🎯 Ключевая механика
1. Создай привычку
2. Собери команду (2-5 человек)
3. Все отмечают выполнение в своем часовом поясе
4. 100% выполнение → стрик растёт
5. Хотя бы один пропустил → стрик сбрасывается

### ✨ Эффекты
- **Социальное давление** — нельзя подвести команду
- **Общая цель** — вместе легче не сдаваться
- **Прозрачность** — видно прогресс каждого

---

## 🏗 Архитектура MVP

```
Frontend (Vue 3)  ←→  Backend (ASP.NET Core)  ←→  Database (PostgreSQL)
                      ↕
                   SignalR Hub
                      ↕
              Real-time синхронизация
```

### Технологический стек

| Компонент | Технология | Обоснование |
|-----------|------------|-------------|
| Backend | ASP.NET Core 8 | Высокая производительность, SignalR из коробки |
| Realtime | SignalR | Мгновенная синхронизация статусов |
| Database | PostgreSQL | Надёжность, работа с UTC временем |
| ORM | EF Core | Удобная работа с сущностями |
| Frontend | Vue 3 + Pinia | Легковесный, реактивный |
| Container | Docker | Единое окружение для всей команды |

---

## 🚀 Быстрый старт

### Предварительные требования
- [Docker](https://www.docker.com/products/docker-desktop) и Docker Compose
- [Git](https://git-scm.com/)

### Запуск проекта

```bash
# 1. Клонируем репозиторий
git clone https://github.com/your-org/duohabit.git
cd duohabit

# 2. Запускаем всё одной командой
docker-compose up -d

# 3. Проверяем логи
docker-compose logs -f

# 4. Открываем в браузере
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000/swagger
# PostgreSQL: localhost:5432
```

### Локальная разработка без Docker

**Backend:**
```bash
cd backend
dotnet restore
dotnet run --project src/Duohabit.API
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Структура проекта

```
duohabit/
├── .github/                    # CI/CD pipelines
├── docs/                       # Документация
├── infrastructure/             # Nginx, настройки
├── backend/
│   ├── src/
│   │   ├── Duohabit.API/      # REST API endpoints
│   │   ├── Duohabit.Core/      # Доменные модели
│   │   ├── Duohabit.Infrastructure/ # Репозитории, EF Core
│   │   └── Duohabit.Hubs/      # SignalR хабы
│   ├── tests/                   # Unit и Integration тесты
│   └── Duohabit.sln
├── frontend/
│   ├── src/
│   │   ├── components/         # Vue компоненты
│   │   ├── views/              # Страницы
│   │   ├── stores/             # Pinia сторы
│   │   ├── services/           # API и SignalR клиенты
│   │   └── utils/              # Хелперы
│   └── package.json
├── docker-compose.yml
└── README.md
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

## 🧪 Тестирование

### Backend
```bash
cd backend
dotnet test
```

### Frontend
```bash
cd frontend
npm run test:unit
```

---

## 📊 Модели данных

### Habit (Привычка)
```json
{
  "id": "uuid",
  "title": "Утренняя пробежка",
  "description": "3 км в парке",
  "ownerId": "uuid",
  "schedule": "daily",
  "deadline": "23:59",
  "groupId": "uuid"
}
```

### HabitPeriod (Период привычки)
```json
{
  "habitId": "uuid",
  "periodKey": "2026-02-28",
  "status": "Pending",
  "calculatedAt": "2026-02-28T23:59:59Z"
}
```

Статусы периода: `Pending` | `Success` | `Failed`

---

## 🔐 Переменные окружения

### Backend (.env)
```env
ConnectionStrings__DefaultConnection=Host=postgres;Database=duohabit;Username=user;Password=pass
ASPNETCORE_ENVIRONMENT=Development
JWT_Secret=your-secret-key-here
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:5000
VITE_SIGNALR_URL=http://localhost:5000/hub
```

---

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Закоммитьте изменения (`git commit -m 'feat: add amazing feature'`)
4. Запушьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

---

## 📝 Полезные команды

### Docker
```bash
# Сборка и запуск
docker-compose up --build

# Остановка
docker-compose down

# Просмотр логов конкретного сервиса
docker-compose logs -f backend

# Очистка всего
docker-compose down -v
```

### Database
```bash
# Подключиться к PostgreSQL
docker exec -it duohabit-postgres-1 psql -U duohabit_user -d duohabit

# Создать миграцию (backend)
dotnet ef migrations add InitialCreate --project src/Duohabit.Infrastructure --startup-project src/Duohabit.API
```

---



**Сделано с ❤️ для тех, кто хочет менять привычки вместе**