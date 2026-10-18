from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Вся конфигурация приходит из переменных окружения."""

    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "postgresql+asyncpg://catalog:catalog@postgres:5432/catalog"

    s3_endpoint_url: str = "http://minio:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "products"
    s3_region: str = "us-east-1"

    bot_token: str = ""
    # Список Telegram ID администраторов через запятую
    admin_ids: str = ""
    webapp_url: str = "http://localhost:8080"
    # webhook | polling | off
    bot_mode: str = "webhook"
    # Публичный базовый URL (https://example.com) для автоустановки вебхука
    webhook_base_url: str = ""
    # Секрет в пути /bot/webhook/{secret} и в заголовке X-Telegram-Bot-Api-Secret-Token
    webhook_secret: str = "change-me-secret"

    max_image_bytes: int = 10 * 1024 * 1024

    @field_validator("admin_ids")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def admin_id_set(self) -> set[int]:
        return {int(x) for x in self.admin_ids.split(",") if x.strip().lstrip("-").isdigit()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
