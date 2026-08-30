"""Configuración de la aplicación, leída desde variables de entorno / .env."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://diegolonio:diegolonio@localhost:5433/diegolonio"
    secret_key: str = "dev-secret-cambiame"
    session_max_age: int = 60 * 60 * 24 * 7  # 7 días, en segundos
    media_dir: str = "media"  # carpeta de imágenes subidas desde el editor
    base_url: str = "https://diegolonio.com"  # para URLs absolutas (sitemap, OpenGraph)

    model_config = {"env_file": ".env"}


settings = Settings()
