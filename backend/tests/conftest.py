"""Shared test configuration."""

import os

# Settings инстанцируются при импорте duohabit.config, поэтому окружение
# должно быть заполнено до первого импорта кода приложения.
# Подключений никуда не происходит: сервисы работают через фейковые репозитории.
os.environ.setdefault("LOG_LEVEL", "CRITICAL")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("REDIS_PASSWORD", "test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ.setdefault("TESTING", "true")
