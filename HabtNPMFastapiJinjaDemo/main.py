"""Точка входа приложения.

Создаёт экземпляр FastAPI, монтирует статику, подключает роутеры.
Запуск: python3 main.py
"""

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import settings
from router import router


def create_app() -> FastAPI:
    """Фабрика приложения: собирает FastAPI и возвращает готовый экземпляр."""
    app = FastAPI(title=settings.app_name, debug=settings.debug)

    # Отдаём CSS/JS из папки static по адресу /static/...
    app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")

    # Все маршруты приложения
    app.include_router(router)

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
