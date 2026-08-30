"""Роутер HTML-страниц.

Каждый эндпоинт рендерит шаблон через общий экземпляр templates.
Логику данных в реальном проекте выносят в сервисный слой; здесь для демо
она простая и лежит прямо в обработчике.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from core.templating import templates

router = APIRouter(tags=["pages"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    features = [
        ("FastAPI", "Современный асинхронный веб-фреймворк на Python."),
        ("Jinja2", "Серверный рендеринг HTML из шаблонов."),
        ("Tailwind CSS", "Utility-first стили прямо в разметке."),
    ]
    return templates.TemplateResponse(
        request,
        "pages/index.html",
        {"title": "Главная", "features": features},
    )


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return templates.TemplateResponse(
        request,
        "pages/about.html",
        {"title": "О проекте"},
    )
