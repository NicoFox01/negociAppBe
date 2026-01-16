from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    DATABASE_URL: str
    SERVICE_ROLE_KEY: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()