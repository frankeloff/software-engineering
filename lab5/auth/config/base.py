from pydantic_settings import BaseSettings, SettingsConfigDict


# ENV settings
class Settings(BaseSettings):
    """
    Класс, описывающий env переменные, указанные в .env файле
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    redis_host: str
    """Адрес БД Редис"""
    redis_port: int
    """Порт БД Редис"""
    redis_password: str
    """Пароль БД Редис"""

    db_port: int
    """Порт БД"""
    db_host: str
    """Хост БД"""
    db_user: str
    """Пользователь БД"""
    db_pass: str
    """Пароль БД"""
    db_name: str
    """Имя БД"""

    postgres_dsn: str
    """Адрес БД"""

settings = Settings(_env_file=".env")  # type: ignore