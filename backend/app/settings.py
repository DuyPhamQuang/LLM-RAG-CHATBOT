from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_url: str = "http://host.docker.internal:11434"

settings = Settings()