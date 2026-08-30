# 03_execution_flow.md
# Логика и работа кода

## Жизненный цикл приложения

### 1. Инициализация

```python
# main.py
app = create_app()
```

При импорте `main.py`:
1. Импортируется `settings` из `core/config.py`.
   - `pydantic-settings` читает `.env` (если существует) и переменные окружения.
   - Создаётся объект `settings` с валидированными полями.
2. Импортируется `router` из `router.py`.
   - `router.py` импортирует `routers/pages.py` и `routers/api.py`.
   - Каждый под-роутер инициализирует свой `APIRouter`.
3. Вызывается `create_app()`:
   - Создаётся `FastAPI(title=settings.app_name, debug=settings.debug)`.
   - Монтируется `StaticFiles` по пути `/static` из `settings.static_dir`.
   - Подключается корневой `router` через `app.include_router(router)`.
4. Готовый объект `app` сохраняется в глобальной переменной.

### 2. Запуск

```python
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
```

- При запуске `python main.py` uvicorn загружает ASGI-callable `main:app`.
- Параметры `host`, `port`, `reload` берутся из `settings`.
- В режиме `debug=True` включена автоматическая перезагрузка при изменении файлов.

### 3. Завершение работы

- Явных обработчиков shutdown (`@app.on_event("shutdown")`, lifespan-контекст) нет.
- Нет открытых соединений с БД, брокерами или внешними сервисами, требующих graceful shutdown.

---

## Ключевые бизнес-процессы

### Процесс 1: Рендеринг главной страницы (`GET /`)

1. Клиент отправляет запрос на `/`.
2. Uvicorn передаёт его FastAPI.
3. FastAPI маршрутизирует запрос в `routers/pages.py::index`.
4. Обработчик формирует локальный список `features`:
   ```python
   features = [
       ("FastAPI", "Современный асинхронный веб-фреймворк на Python."),
       ("Jinja2", "Серверный рендеринг HTML из шаблонов."),
       ("Tailwind CSS", "Utility-first стили прямо в разметке."),
   ]
   ```
5. Вызывается `templates.TemplateResponse(request, "pages/index.html", {"title": "Главная", "features": features})`.
6. Jinja2:
   - Загружает `templates/pages/index.html`.
   - Применяет `{% extends "base.html" %}`.
   - Подставляет блоки `title` и `content`.
   - В `base.html` выполняет `{% include "partials/navbar.html" %}` и `{% include "partials/footer.html" %}`.
   - Подставляет глобальную переменную `app_name` из `core/templating.py`.
7. Сформированный HTML возвращается клиенту с `Content-Type: text/html`.

### Процесс 2: Рендеринг страницы "О проекте" (`GET /about`)

1. Клиент отправляет запрос на `/about`.
2. Запрос маршрутизируется в `routers/pages.py::about`.
3. Обработчик вызывает `templates.TemplateResponse(request, "pages/about.html", {"title": "О проекте"})`.
4. Jinja2 рендерит шаблон аналогично главной странице.
5. HTML возвращается клиенту.

### Процесс 3: Вызов JSON API (`GET /api/ping`)

1. Клиент (браузерный JS или внешний клиент) отправляет запрос на `/api/ping`.
2. Запрос попадает в роутер `routers/api.py` благодаря префиксу `prefix="/api"`.
3. Выполняется обработчик `ping()`:
   ```python
   return {"status": "ok", "message": "pong"}
   ```
4. FastAPI сериализует словарь в JSON и возвращает ответ с `Content-Type: application/json`.

### Процесс 4: Клиентский вызов API из браузера

1. Браузер загружает главную страницу.
2. Подключается `static/js/main.js`.
3. После `DOMContentLoaded` скрипт находит кнопку `#ping-btn` и элемент `#ping-result`.
4. По клику выполняется `fetch('/api/ping')`.
5. Ответ парсится как JSON, результат выводится в `#ping-result`.
6. При ошибке сети выводится сообщение "Ошибка запроса".

---

## Роутинг и middleware

### Роутинг

| Путь | Метод | Обработчик | Тип ответа |
|---|---|---|---|
| `/` | `GET` | `routers/pages.py::index` | `HTMLResponse` |
| `/about` | `GET` | `routers/pages.py::about` | `HTMLResponse` |
| `/api/ping` | `GET` | `routers/api.py::ping` | JSON (автоматически) |
| `/static/...` | `GET` | `StaticFiles` | Статические файлы |
| `/docs` | `GET` | FastAPI Swagger UI | HTML |
| `/redoc` | `GET` | FastAPI ReDoc | HTML |
| `/openapi.json` | `GET` | FastAPI OpenAPI schema | JSON |

### Подключение роутеров

```python
# router.py
router = APIRouter()
router.include_router(pages.router)
router.include_router(api.router)

# main.py
app.include_router(router)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")
```

### Middleware

- **Стандартные middleware FastAPI** активны по умолчанию: обработка ошибок, CORS отсутствует (не настроен), парсинг запросов, валидация зависимостей.
- **Пользовательских middleware не зарегистрировано**.
- **CORS не включён**: при размещении фронтенда на другом домене запросы будут заблокированы браузером.

---

## Обработка ошибок и логирование

### Обработка ошибок

- Используется встроенный механизм FastAPI:
  - `HTTPException` → стандартный JSON-ответ с кодом ошибки.
  - Ошибки валидации Pydantic → `422 Unprocessable Entity`.
  - Необработанные исключения → `500 Internal Server Error` с трассировкой (в режиме `debug=True`) или общим сообщением (в режиме `debug=False`).
- **Пользовательских обработчиков исключений (`@app.exception_handler`) нет**.

### Логирование

- Явного логирования в коде приложения нет.
- Uvicorn ведёт access-логи и логи сервера в `stdout`/`stderr`.
- В `Dockerfile` установлен `PYTHONUNBUFFERED=1`, чтобы логи сразу попадали в вывод контейнера.
- Уровень логирования не настраивается через `settings`.

---

## Особенности запуска в контейнере

- `compose.yaml` использует внешнюю сеть `internal` (должна быть создана заранее: `docker network create internal`).
- Порты наружу не пробрасываются; сервис доступен только внутри сети Docker по адресу `app:8000`.
- `HOST=0.0.0.0` обязателен в контейнере, иначе Uvicorn будет слушать только `127.0.0.1` и станет недоступен извне контейнера.
- `DEBUG=false` отключает reload внутри контейнера.

# End of 03_execution_flow.md
