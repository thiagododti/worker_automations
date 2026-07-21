from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    broker_url: str
    result_backend: str
    automacao: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # Instância global de configuração para a aplicação.
