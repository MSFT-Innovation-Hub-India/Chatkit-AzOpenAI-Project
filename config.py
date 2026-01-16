"""
Configuration module for ChatKit Todo App.
Loads settings from environment variables with Azure OpenAI support.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Azure OpenAI Configuration
    azure_openai_endpoint: str = Field(
        default="",
        alias="AZURE_OPENAI_ENDPOINT",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_deployment: str = Field(
        default="gpt-4o",
        alias="AZURE_OPENAI_DEPLOYMENT",
        description="Azure OpenAI deployment name"
    )
    azure_openai_api_version: str = Field(
        default="2025-01-01-preview",
        alias="AZURE_OPENAI_API_VERSION",
        description="Azure OpenAI API version"
    )
    
    # Application Configuration
    app_host: str = Field(
        default="0.0.0.0",
        alias="APP_HOST",
        description="Host to bind the application"
    )
    app_port: int = Field(
        default=8000,
        alias="APP_PORT",
        description="Port to bind the application"
    )
    
    # Data Store Configuration
    data_store_path: str = Field(
        default="./data/chatkit.db",
        alias="DATA_STORE_PATH",
        description="Path to SQLite database file"
    )
    
    # Logging
    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL",
        description="Logging level"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


# Global settings instance
settings = Settings()
