from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    youtube_video_id_pattern: str = ""
    youtube_api_key: str = ""
    youtube_api_url: str = ""
    redis_host: str = "localhost"
    redis_port: int = 6379
    jwt_secret_key: str = ""
    jwt_refresh_key: str = ""
    psql_host: str = "localhost"
    psql_port: int = 5432
    psql_user: str = ""
    psql_password: str = ""
    google_client_id: str = "",
    google_client_secret: str = "",
    secret_key: str = ""
    smtp_server: str = "localhost"
    smtp_port: int
    gmail_user: str = ""
    gmail_password: str = ""
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int

settings = AppSettings()

RABBITMQ_URL = f"amqp://{settings.rabbitmq_host}:{settings.rabbitmq_port}/"
DATABASE_URL = f"postgresql+asyncpg://{settings.psql_user}:{settings.psql_password}@{settings.psql_host}:{settings.psql_port}/content_api"

