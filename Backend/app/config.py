from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    exogena_files_dir: str = "exogena_files"
    uvt_api_url: str = "https://uvt.com.co/"
    uvt_simulador_url: str = "http://127.0.0.1:8000"
    uvt_intervalo_segundos: int = 21600

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings():
    return DbSettings()
