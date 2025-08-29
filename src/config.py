# --------------------------------------------------
# config.py
# --------------------------------------------------

from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # DynamoDB
    DYNAMO_ENDPOINT: str = Field(default="http://localhost:8000", env="DYNAMO_ENDPOINT")
    DYNAMO_TABLE: str = Field(default="awsproject-store", env="DYNAMO_TABLE")

    # Constrols para testes do Circuit Breaker / fail injection
    # FORCE_FAIL_ALWAYS: se True, qualuqer prompt contendo "fail" sempre falhará
    FORCE_FAIL_ALWAYS: bool = Field(default=False, env="FORCE_FAIL_ALWAYS")
    # Probabilidade de falha quando FORCE_FAIL_ALWAYS==False (0.0..1.0)
    FORCE_FAIL_PERCENT: float = Field(default=0.7, env="FORCE_FAIL_PERCENT")

    # Ambiente
    ENV: str = Field(default="dev", env="ENV")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instância global para importar rm todo o projeto
settings = Settings()