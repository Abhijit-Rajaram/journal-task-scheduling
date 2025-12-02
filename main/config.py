from pydantic import BaseSettings

class Settings(BaseSettings):
    EMAIL_HOST: str
    EMAIL_PORT: int
    EMAIL_ADDRESS: str
    EMAIL_PASSWORD: str

    DATABASE_URL: str
    TIMEZONE: str = "UTC"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
