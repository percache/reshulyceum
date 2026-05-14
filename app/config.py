from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ReshuLyceum"
    database_url: str = "sqlite:///./reshulyceum.db"
    secret_key: str = "change-me-in-prod-please-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
