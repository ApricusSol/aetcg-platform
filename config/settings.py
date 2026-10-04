from pydantic_settings import BaseSettings
from pydantic import Field, validator
import os
from typing import Optional


class AppSettings(BaseSettings):
    APP_ENV: str = Field(default="development", description="Application environment (development/production)")
    API_PORT: int = Field(default=8000, description="API service port", ge=1, le=65535)
    REDIS_HOST: str = Field(default="queue_broker", description="Redis host for queue broker")
    REDIS_PORT: int = Field(default=6379, description="Redis port", ge=1, le=65535)
    EXTERNAL_COMPLIANCE_API_URL: str = Field(
        default="https://api.mockcompliance.org/v1/validate",
        description="External compliance API endpoint"
    )
    EXTERNAL_API_TIMEOUT_SEC: float = Field(
        default=5.0,
        description="Timeout for external API calls in seconds",
        gt=0
    )

    LLM_ENDPOINT_URL: str = Field(
        default="https://studio.bearcatgpt.uc.edu/api/v1/",
        description="LLM service endpoint URL"
    )
    LLM_ACCESS_TOKEN: str = Field(
        default="",
        description="Access token for LLM service"
    )

    # Security-related settings
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Maximum API requests per minute per IP",
        gt=0
    )
    SUPERVISOR_TOKEN: str = Field(
        default="SECURE_GOVERNANCE_TOKEN_XYZ",
        description="Token for supervisor approval endpoint"
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    @validator('APP_ENV')
    def validate_app_env(cls, v):
        allowed_envs = ['development', 'staging', 'production']
        if v not in allowed_envs:
            raise ValueError(f'APP_ENV must be one of {allowed_envs}')
        return v

    @validator('LLM_ACCESS_TOKEN')
    def validate_llm_token(cls, v):
        # In production, token should not be empty
        # This is a soft warning - in real implementation might check APP_ENV
        if not v and os.getenv('APP_ENV') == 'production':
            # In a real implementation, we might raise an error or log a warning
            pass
        return v

settings = AppSettings()
