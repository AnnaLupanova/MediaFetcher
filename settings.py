from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    youtube_video_id_pattern: str = ""
    youtube_api_key: str = ""
    youtube_api_url: str = ""
    redis_url: str = "localhost"
    jwt_secret_key: str = ""
    jwt_refresh_key: str = ""
    google_client_id: str = "",
    google_client_secret: str = "",
    secret_key: str = ""
    smtp_server: str = "localhost"
    smtp_port: int
    gmail_user: str = ""
    gmail_password: str = ""
    celery_broker_url: str = "localhost"
    celery_result_backend: str = "localhost"
    database_url: str = "localhost"
    rabbitmq_url: str = "localhost"

settings = AppSettings()