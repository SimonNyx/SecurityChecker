from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    encryption_key: str
    openwebui_base_url: str = "http://localhost:3000"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8

settings = Settings()
