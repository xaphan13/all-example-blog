# my_blog_docs — документация по моим проектам

Этот репозиторий — **коллекция документации** для 6 проектов на стеке FastAPI/Python.
Исходного кода здесь нет: в каждой папке лежат `AGENTS.md` (правила для AI-агентов),
`README` (описание проекта) и `docs/` (подробная документация).

## Проекты

| Папка | Проект | Стек | Коротко |
|---|---|---|---|
| [`AmiaBlog/`](AmiaBlog/) | Простая блог-система | Python 3.11+, FastAPI, MDUIv2, SQLite (поиск) | Markdown-посты, i18n, RSS, генерация статического сайта, hot-reload контента |
| [`diegolonio-dot-com/`](diegolonio-dot-com/) | Персональный блог и портфолио | Python 3.14, FastAPI, PostgreSQL, чистый SQL | Без ORM и CMS; встроенный markdown-редактор, админ-панель |
| [`fastapi-htmx-starter/`](fastapi-htmx-starter/) | Стартовый шаблон веб-приложений | Python 3.12+, FastAPI, HTMX, Tailwind, SQLAlchemy 2 | Готовая аутентификация, CRUD-пример, Alembic, CLI-команды |
| [`fastAPIuser-suren/`](fastAPIuser-suren/) | Подсистема управления пользователями | Python 3.12+, FastAPI, PostgreSQL 17, Redis 8 | fastapi-users, верификация email, сброс пароля, роли, Redis-кэш, вебхуки, email |
| [`HabtNPMFastapiJinjaDemo/`](HabtNPMFastapiJinjaDemo/) | Демо для статьи: FastAPI + Jinja2 + Tailwind | Python 3.12, FastAPI, Jinja2, Tailwind (CDN) | Stateless-приложение, чистая слоистая архитектура SSR |
| [`luovkle.com/`](luovkle.com/) | Персональный блог и портфолио | Python 3.13+, FastAPI, Jinja2, Tailwind, Podman/Caddy | SSR без БД; контент в Markdown; двойной рендеринг: HTML + ANSI-арт для `curl` |

## Структура каждой папки

```
<проект>/
├── AGENTS.md / AGENTS.ru.md   # правила работы AI-агентов с проектом
├── README.md / README.ru.md   # описание проекта для людей
└── docs/                      # подробная документация
    ├── 01_project_structure.md
    ├── 02_architecture.md
    ├── 03_execution_flow.md
    ├── 04_code_quality.md
    ├── 05_optimization_roadmap.md
    └── ... (специфика проекта)
```

## Как пользоваться

- **Людям:** начните с `README` нужной папки, затем читайте `docs/` по порядку.
- **AI-агентам:** начните с корневого [`AGENTS.md`](AGENTS.md) — там карта всех
  проектов, правила поиска информации и сценарии работы; затем переходите к
  `AGENTS.md` конкретного проекта.
