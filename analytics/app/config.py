from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mysql_host: str = "mysql"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "lintel@365"
    mysql_database: str = "symphony"

    whisper_url: str = "http://whisper:8001"
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "mistral:7b"

    recordings_dir: str = "/recordings"
    batch_interval_seconds: int = 60

    class Config:
        env_file = ".env"


settings = Settings()
