from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SERVICE_ROLE_KEY: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NegociApp"

    class Config:
        env_file = ".env"
        extra = "ignore"
settings = Settings()