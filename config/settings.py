from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    APP_ENV: str = "development"
    API_PORT: int = 8000
    REDIS_HOST: str = "queue_broker"
    REDIS_PORT: int = 6379
    EXTERNAL_COMPLIANCE_API_URL: str = "https://api.mockcompliance.org/v1/validate"
    EXTERNAL_API_TIMEOUT_SEC: float = 5.0

    LLM_ENDPOINT_URL: str = "https://studio.bearcatgpt.uc.edu/api/v1/"
    LLM_ACCESS_TOKEN: str = ""

    model_config = {"env_file": ".env"}

settings = AppSettings()
