# /itsm_agent/config.py

import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Loads configuration from environment variables."""
    # LLM Provider Configuration
    # You can point this to OpenAI or any other compatible API endpoint
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4-turbo"

    # External Service URLs (for the agent's tools)
    RAG_SERVER_URL: str = "http://localhost:8001/get_suggestion"
    ESDB_URL: str = "http://localhost:9200" # Example Elasticsearch URL
    STARDUST_API_URL: str = "http://api.stardust.internal/v1"

    class Config:
        # This allows loading variables from a .env file for local development
        env_file = ".env"
        env_file_encoding = 'utf-8'

# Create a single settings instance to be imported by other modules
settings = Settings()