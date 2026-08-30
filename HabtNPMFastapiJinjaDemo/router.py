"""Корневой агрегатор роутеров.

main.py подключает единственный объект `router`, а сюда стекаются все
под-роутеры приложения. Добавили новый модуль в routers/ — дописали одну
строку include_router, и больше main.py трогать не нужно.
"""

from fastapi import APIRouter

from routers import api, pages

router = APIRouter()

router.include_router(pages.router)
router.include_router(api.router)
