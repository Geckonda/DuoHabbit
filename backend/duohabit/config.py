"""Environment config."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """App Settings. Leave deployment, not business logic up to environment."""

    redis_host: str
    redis_port: int
    redis_password: str

    postgres_host: str
    postgres_port: int
    postgres_password: str
    postgres_user: str
    postgres_db: str

    jwt_secret: str

    # Пустая строка по умолчанию - notify() тихо отключает пуши, если ключей нет
    # (локальный dev, тесты), не требуя их для запуска приложения
    vapid_public_key: str = ""
    vapid_private_key: str = ""
    vapid_subject: str = "mailto:admin@duohabit.com"

    session_lifetime: int = 3600 * 24 * 30  # 30 days

    testing: bool = False

    def get_postgres_url(self) -> str:
        """Get the PostgreSQL connection URL from the environment."""
        postgres_addr = f"{self.postgres_host}:{self.postgres_port}"
        postgres_auth = f"{self.postgres_user}:{self.postgres_password}"
        return (
            f"postgresql+asyncpg://{postgres_auth}@{postgres_addr}/{self.postgres_db}"
        )


settings = Settings()
