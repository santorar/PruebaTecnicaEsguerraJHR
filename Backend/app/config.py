from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    exogena_files_dir: str = "exogena_files"
    uvt_api_url: str = "https://uvt.com.co/"
    uvt_simulador_url: str = "http://127.0.0.1:8000"
    uvt_intervalo_segundos: int = 604800

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    secret_key: str = "cambiar-en-produccion"
    token_segundos: int = 86400

    model_config = SettingsConfigDict(env_file=".env")

    @property
    def origenes_permitidos(self) -> list[str]:
        return [origen.strip() for origen in self.cors_origins.split(",") if origen.strip()]


@lru_cache
def get_settings():
    return DbSettings()
