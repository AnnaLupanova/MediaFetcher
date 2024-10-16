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

settings = AppSettings()
