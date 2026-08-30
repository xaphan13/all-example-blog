"""Пример JSON API.

Демонстрирует, что в одном приложении уживаются и HTML-страницы, и REST-эндпоинты.
Все маршруты вынесены под префикс /api.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/ping")
async def ping():
    return {"status": "ok", "message": "pong"}
