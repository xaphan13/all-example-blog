# AGENTS.md — инструкция для AI-агентов

## ⚠️ Важно: документация уже существует

В этом проекте **уже есть подробная документация** — сначала прочитай её, прежде
чем делать выводы о проекте или вносить изменения:

| Файл | Что внутри |
|------|------------|
| [docs/01_project_structure.md](docs/01_project_structure.md) | Карта проекта: дерево директорий, ответственность каждого файла, все зависимости |
| [docs/02_architecture.md](docs/02_architecture.md) | Слоистая архитектура, паттерны, схемы потока данных, переменные окружения |
| [docs/03_execution_flow.md](docs/03_execution_flow.md) | Жизненный цикл приложения, обработка запросов, роутинг, ошибки, запуск в Docker |
| [docs/04_code_quality.md](docs/04_code_quality.md) | Анализ по SOLID/DRY/KISS, технический долг, безопасность, узкие места |
| [docs/05_tailwind_cdn_vs_production.md](docs/05_tailwind_cdn_vs_production.md) | Tailwind CDN vs production-сборка: компромиссы и пошаговая миграция |
| [docs/06_frontend.md](docs/06_frontend.md) | Отчёт по фронтенду: шаблоны, верстка, стили, клиентский JS, оценка качества |

Краткое описание для людей — в [README.md](README.md) (на русском языке).
Этот файл (`AGENTS.md`) — рабочая памятка для AI-агентов.

**Правило:** если изменил структуру, конфигурацию или поведение приложения —
актуализируй соответствующий файл в `docs/` и README.

---

## О проекте

Демонстрационный веб-проект для статьи: **FastAPI + Jinja2 + Tailwind CSS**.
Цель — не функциональность, а чистая, масштабируемая архитектура
серверного рендеринга. Приложение stateless: без БД, кэша, аутентификации
и внешних сервисов (кроме Tailwind CDN).

**Стек:** FastAPI 0.137.0, Uvicorn 0.49.0 (`[standard]`), Jinja2 3.1.6,
pydantic-settings 2.14.1, python-multipart 0.0.32, Tailwind CSS (CDN).
Python 3.12.

**Эндпоинты:**

| Путь | Тип | Обработчик |
|------|-----|------------|
| `GET /` | HTML | `routers/pages.py::index` |
| `GET /about` | HTML | `routers/pages.py::about` |
| `GET /api/ping` | JSON | `routers/api.py::ping` → `{"status": "ok", "message": "pong"}` |
| `/static/...` | файлы | `StaticFiles` (монтируется в `main.py`) |
| `/docs`, `/redoc` | HTML | Swagger UI / ReDoc от FastAPI |

---

## Структура (кратко)

```
main.py        — фабрика create_app() + запуск uvicorn под if __name__ == "__main__"
router.py      — агрегатор: include_router для всех под-роутеров из routers/
core/
  config.py    — Settings (pydantic-settings), единый объект settings
  templating.py— единый экземпляр Jinja2Templates + глобальные переменные шаблонов
routers/
  pages.py     — HTML-страницы (тег "pages")
  api.py       — JSON API, префикс /api (тег "api")
static/        — css/style.css (поверх Tailwind), js/main.js (fetch /api/ping)
templates/
  base.html    — layout, здесь подключается Tailwind CDN
  partials/    — navbar.html, footer.html ({% include %})
  pages/       — index.html, about.html ({% extends "base.html" %})
docs/          — подробная документация (см. таблицу выше)
Dockerfile     — python:3.12-slim, CMD ["python", "main.py"]
compose.yaml   — сервис app во ВНЕШНЕЙ сети internal, порты наружу НЕ пробрасываются
```

---

## Команды

```bash
# Локальный запуск (venv в ./venv)
pip install -r requirements.txt
python3 main.py                # → http://127.0.0.1:8000, reload при DEBUG=true

# Docker
docker network create internal # внешняя сеть обязательна
docker compose up --build      # сервис доступен как app:8000 внутри сети internal
```

Тестов в проекте нет. Проверка вручную: открыть `/`, нажать кнопку Ping
(должен отработать `fetch('/api/ping')`), проверить `/docs`.

---

## Конфигурация

Через переменные окружения / `.env` (читаются в `core/config.py`):
`APP_NAME`, `DEBUG` (default `true`), `HOST` (default `127.0.0.1`),
`PORT` (default `8000`), `STATIC_DIR`, `TEMPLATES_DIR`.

В `compose.yaml` принудительно заданы `HOST=0.0.0.0`, `PORT=8000`, `DEBUG=false`.

---

## Правила и конвенции (обязательны при изменениях)

1. **Комментарии и докстринги — на русском языке** (так принято во всём проекте).
2. **Фабрика приложения.** Вся сборка FastAPI — внутри `create_app()` в `main.py`.
   Не создавать глобальный `app` иначе как через `app = create_app()`.
3. **Новые маршруты** — только через новый модуль в `routers/` + одна строка
   `include_router` в `router.py`. Ничего не добавлять прямо в `main.py`.
4. **HTML и JSON раздельно:** страницы — в `routers/pages.py`, API — под
   префиксом `/api` со своим тегом.
5. **Конфигурация** — только через `Settings` в `core/config.py`. Никаких
   магических констант (хост, порт, пути) в коде.
6. **Шаблоны:** наследование от `base.html` + блоки `title`/`content`,
   повторяющиеся куски — в `partials/`. Не дублировать `<head>`.
7. **Современный API:** `templates.TemplateResponse(request, "name.html", {...})`
   — `request` первым аргументом. Старая сигнатура устарела.
8. **Асинхронность:** обработчики — `async def`.
9. **Пути** — через `pathlib.Path`, а не строки.
10. **Tailwind через CDN** — осознанное решение для демо (обоснование и план
    миграции в `docs/05_tailwind_cdn_vs_production.md`). Не «чинить» это без
    явного запроса пользователя.

## Типовые задачи

- **Новая страница:** обработчик в `routers/pages.py` + шаблон в `templates/pages/`.
- **Новый API-раздел:** модуль в `routers/` + `include_router` в `router.py`.
- **Бизнес-логика:** по мере роста выносить из обработчиков в слой `services/`
  (сейчас его нет — это сознательное упрощение).
- **Новый параметр конфигурации:** поле в `Settings` + строка в таблице
  переменных окружения в `docs/02_architecture.md` и README.
- **Изменение структуры файлов:** обновить дерево в `docs/01_project_structure.md`,
  README и в этом файле.
