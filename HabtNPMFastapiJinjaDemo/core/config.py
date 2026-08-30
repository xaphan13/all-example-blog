"""Конфигурация приложения.

Все настройки читаются из переменных окружения (или файла .env) через
pydantic-settings. Это даёт валидацию типов и единую точку конфигурации.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта: .../NPMPythonDemoProject
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Метаданные приложения
    app_name: str = "FastAPI + Jinja2 + Tailwind Demo"
    debug: bool = True

    # Параметры запуска uvicorn
    host: str = "127.0.0.1"
    port: int = 8000

    # Пути до статики и шаблонов
    static_dir: Path = BASE_DIR / "static"
    templates_dir: Path = BASE_DIR / "templates"


# Единственный экземпляр настроек на всё приложение
settings = Settings()
