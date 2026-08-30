"""Единая точка работы с Jinja2.

Здесь создаётся один экземпляр Jinja2Templates, который импортируют роутеры.
Так настройки шаблонизатора (папка, глобальные переменные, фильтры) живут
в одном месте, а не дублируются по эндпоинтам.
"""

from fastapi.templating import Jinja2Templates

from core.config import settings

templates = Jinja2Templates(directory=settings.templates_dir)

# Глобальные переменные, доступные во всех шаблонах без передачи в context.
templates.env.globals["app_name"] = settings.app_name
