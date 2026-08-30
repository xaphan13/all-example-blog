# 02_architecture.md
# Архитектура и паттерны

## Высокоуровневая архитектура

Проект представляет собой **классический монолитный веб-сервер** с серверным рендерингом и лёгким JSON API. Архитектура **слоиcтая (layered)**:

```
┌─────────────────────────────────────────────────────────────┐
│  Presentation / Transport Layer                              │
│  - FastAPI (ASGI-app)                                        │
│  - routers/pages.py  → HTML-ответы                           │
│  - routers/api.py    → JSON-ответы                           │
├─────────────────────────────────────────────────────────────┤
│  Template Layer                                              │
│  - Jinja2Templates (core/templating.py)                      │
│  - templates/                                                │
├─────────────────────────────────────────────────────────────┤
│  Configuration / Infrastructure Layer                        │
│  - core/config.py    → pydantic-settings                     │
│  - core/templating.py→ настройка шаблонизатора               │
├─────────────────────────────────────────────────────────────┤
│  Runtime / Deployment Layer                                  │
│  - uvicorn (ASGI-server)                                     │
│  - Docker / Docker Compose                                   │
└─────────────────────────────────────────────────────────────┘
```

Отдельного сервисного слоя (`services/`), слоя доступа к данным (`repositories/`) и моделей предметной области нет: это сознательное упрощение демо-проекта.

---

## Основные паттерны проектирования

### 1. Фабрика приложения (Application Factory)

- Реализация: `main.py::create_app()`
- Смысл: создание экземпляра `FastAPI` инкапсулировано в функции. Это упрощает тестирование (можно создавать изолированные экземпляры с разными настройками), исключает side-эффекты при импорте и даёт явную точку сборки приложения.

### 2. Единая точка конфигурации (Single Source of Truth для настроек)

- Реализация: `core/config.py::Settings`, глобальный объект `settings`
- Смысл: все параметры приложения (хост, порт, пути, debug, имя приложения) централизованы, валидируются через `pydantic-settings`, читаются из переменных окружения или `.env`.

### 3. Singleton для инфраструктурных объектов

- Реализация: `core/templating.py::templates`
- Смысл: один экземпляр `Jinja2Templates` используется всеми роутерами. Глобальные переменные шаблонов (`app_name`) задаются в одном месте.

### 4. Агрегация роутеров (Router Aggregation)

- Реализация: `router.py`
- Смысл: `main.py` подключает один корневой `APIRouter`, а детали подключения конкретных модулей скрыты в `router.py`. Добавление нового раздела не требует изменения `main.py`.

### 5. Разделение ответственности между `pages` и `api`

- Реализация: `routers/pages.py`, `routers/api.py`
- Смысл: HTML-страницы и JSON-эндпоинты разнесены по разным роутерам с разными тегами и префиксами. Это облегчает эволюцию API и страниц независимо друг от друга.

### 6. Шаблонное наследование и партиалы (DRY на уровне разметки)

- Реализация: `templates/base.html`, `templates/pages/*.html`, `templates/partials/*.html`
- Смысл: общий layout определён в `base.html`, страницы переопределяют только блоки `title`/`content`, повторяющиеся элементы (navbar, footer) вынесены в partials.

---

## Схема потока данных (Data Flow)

### HTTP-запрос к HTML-странице

```
Клиент
  │
  ▼
Uvicorn (ASGI-server)
  │
  ▼
FastAPI app (main.py::app)
  │
  ▼
StaticFiles middleware (для /static/...)  ──► static/css/style.css, static/js/main.js
  │
  ▼
Корневой router.py
  │
  ▼
routers/pages.py
  │
  ▼
core/templating.py::templates
  │
  ▼
Jinja2 рендерит templates/pages/index.html
  │
  ▼
HTML-ответ клиенту
```

### HTTP-запрос к JSON API

```
Клиент
  │
  ▼
Uvicorn
  │
  ▼
FastAPI app
  │
  ▼
router.py
  │
  ▼
routers/api.py::ping
  │
  ▼
JSON-ответ {"status": "ok", "message": "pong"}
```

### Жизненный цикл конфигурации

```
Импорт core/config.py
  │
  ▼
Settings() читает .env / переменные окружения
  │
  ▼
settings используется в:
  - main.py (host, port, debug, app_name, static_dir)
  - core/templating.py (templates_dir, app_name)
  - router-ах (косвенно через templates)
```

---

## Управление состоянием, кэшированием и конфигурацией

### Состояние

- Приложение **stateless**.
- Нет сессий, кук, кэша, базы данных, распределённого состояния.
- Все данные (`features` в `routers/pages.py`) создаются заново при каждом запросе.

### Кэширование

- Кэширование **не реализовано**.
- Статика отдаётся через `StaticFiles` без настройки cache-control; браузер полагается на стандартное поведение.
- Шаблоны Jinja2 компилируются при первом использовании внутри `Jinja2Templates`, но явного кэширования на уровне приложения нет.

### Конфигурация

- Все параметры централизованы в `core/config.py`.
- Используется `pydantic-settings`:
  - `env_file=".env"` — чтение из файла `.env`.
  - Значения по умолчанию для всех полей (например, `host="127.0.0.1"`, `port=8000`, `debug=True`).
- Переменные окружения в `compose.yaml` переопределяют значения по умолчанию (`HOST=0.0.0.0`, `DEBUG=false`).

### Переменные окружения

| Переменная | Тип | Значение по умолчанию | Где используется |
|---|---|---|---|
| `APP_NAME` | `str` | `"FastAPI + Jinja2 + Tailwind Demo"` | `main.py`, `core/templating.py` |
| `DEBUG` | `bool` | `True` | `main.py` |
| `HOST` | `str` | `"127.0.0.1"` | `main.py` |
| `PORT` | `int` | `8000` | `main.py` |
| `STATIC_DIR` | `Path` | `BASE_DIR / "static"` | `main.py` |
| `TEMPLATES_DIR` | `Path` | `BASE_DIR / "templates"` | `core/templating.py` |

# End of 02_architecture.md
