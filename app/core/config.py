from typing import Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = Field(
        default="YouTube Social Media Analysis API",
        description="API title for documentation"
    )
    API_VERSION: str = Field(
        default="1.0.0", 
        description="API version"
    )
    
    # YouTube API Configuration (RapidAPI)
    YOUTUBE_RAPIDAPI_KEY: str = Field(
        ...,
        env="YOUTUBE_RAPIDAPI_KEY",
        description="YouTube RapidAPI key (required)",
        min_length=10
    )
    YOUTUBE_RAPIDAPI_HOST: str = Field(
        default="youtube138.p.rapidapi.com",
        env="YOUTUBE_RAPIDAPI_HOST",
        description="YouTube RapidAPI host"
    )
    YOUTUBE_BASE_URL: str = Field(
        default="https://youtube138.p.rapidapi.com",
        env="YOUTUBE_BASE_URL",
        description="YouTube API base URL"
    )
    
    # AI Configuration
    OPENAI_API_KEY: str = Field(
        ...,
        env="OPENAI_API_KEY", 
        description="OpenAI API key (required)",
        min_length=20
    )
    DEFAULT_MODEL: str = Field(
        default="gpt-4.1-2025-04-14",
        env="DEFAULT_MODEL",
        description="Default OpenAI model to use"
    )
    
    # Authentication
    SERVICE_API_KEY: str = Field(
        ...,
        env="SERVICE_API_KEY",
        description="API key for service authentication (required)",
        min_length=16
    )
    
    # Processing Limits
    MAX_VIDEOS_PER_REQUEST: int = Field(
        default=50,
        env="MAX_VIDEOS_PER_REQUEST",
        description="Maximum videos per request",
        ge=1, le=100
    )
    DEFAULT_VIDEOS_PER_REQUEST: int = Field(
        default=20,
        env="DEFAULT_VIDEOS_PER_REQUEST", 
        description="Default number of videos per request",
        ge=1, le=50
    )
    MAX_COMMENTS_PER_VIDEO: int = Field(
        default=50,
        env="MAX_COMMENTS_PER_VIDEO",
        description="Maximum comments to collect per video",
        ge=10, le=100
    )
    
    # Request Configuration  
    REQUEST_TIMEOUT: float = Field(
        default=30.0,
        env="REQUEST_TIMEOUT",
        description="HTTP request timeout in seconds",
        ge=10.0, le=120.0
    )
    YOUTUBE_REQUEST_DELAY: float = Field(
        default=0.5,
        env="YOUTUBE_REQUEST_DELAY",
        description="Delay between YouTube API requests in seconds",
        ge=0.0, le=5.0
    )
    
    # Environment
    ENVIRONMENT: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment"
    )
    
    # Server Configuration
    PORT: int = Field(
        default=8000,
        env="PORT",
        description="Port for the server to listen on",
        ge=1, le=65535
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
