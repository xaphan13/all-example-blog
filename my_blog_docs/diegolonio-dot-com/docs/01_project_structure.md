# Карта проекта

## Назначение

`diegolonio.com` — персональный блог и портфолио Diego Villegas. Сайт построен как небольшое серверное веб-приложение с упором на минимализм инструментария: без ORM, без frontend-фреймворков, без CMS. Контент создаётся через встроенную админ-панель с markdown-редактором и сохраняется в PostgreSQL; HTML-контент кешируется в БД при сохранении.

Проект ориентирован на self-hosted развёртывание через Docker Compose на домашнем сервере за Cloudflare Tunnel. Деплой предполагает ручное управление секретами, миграциями и бэкапами.

## Дерево директорий и ключевые файлы

```
.
├── app/                        # Исходный код приложения
│   ├── main.py                 # Точка входа FastAPI: lifespan, роуты, статика, 404
│   ├── config.py               # Pydantic-конфигурация из переменных окружения / .env
│   ├── database.py             # Пул psycopg 3 и зависимость get_db для FastAPI
│   ├── auth.py                 # Хеширование паролей, signed cookie-сессии, зависимость require_admin
│   ├── templating.py           # Общий экземпляр Jinja2Templates + глобальные фильтры
│   ├── markdown_render.py      # Pipeline markdown → HTML (Pygments, KaTeX, dollarmath)
│   ├── media_cleanup.py        # Удаление неиспользуемых изображений из media/
│   ├── projects.py             # Загрузка списка проектов из projects.yaml
│   ├── slugs.py                # Генерация и дедупликация slug для постов
│   ├── queries/                # Чистые SQL-запросы по сущностям
│   │   ├── posts.py            # CRUD, full-text search, пагинация постов
│   │   ├── tags.py             # Теги и связь post_tags
│   │   └── users.py            # Аутентификация пользователей
│   ├── routers/                # Маршруты FastAPI
│   │   ├── public.py           # Публичные страницы: home, post, about, search, sitemap, robots
│   │   └── admin.py            # Админ-панель: login/logout, CRUD постов, preview, загрузка изображений
│   ├── templates/              # Jinja2-шаблоны
│   │   ├── base.html           # Базовый layout (SEO, OG, навигация)
│   │   ├── index.html          # Главная с пагинацией
│   │   ├── post.html           # Страница поста
│   │   ├── about.html          # О себе и проекты
│   │   ├── search.html         # Поисковая страница
│   │   ├── tag.html            # Посты по тегу
│   │   ├── 404.html            # Кастомная страница 404
│   │   ├── _post_cards.html    # Partial карточек постов
│   │   └── admin/              # Шаблоны админки
│   │       ├── base_admin.html
│   │       ├── login.html
│   │       ├── manager.html
│   │       └── form.html
│   └── static/                 # Статика
│       ├── css/                # Vanilla CSS (base, home, post, pygments, admin, search, about)
│       ├── js/                 # editor.js — markdown-редактор и загрузка изображений
│       └── img/                # Изображения сайта (favicon, профиль)
├── migrations/                 # SQL-миграции
│   ├── 001_initial.sql         # Начальная схема БД
│   └── run_migrations.py       # Идемпотентный runner миграций
├── scripts/                    # Утилиты
│   ├── create_admin.py         # Создание/обновление администратора
│   ├── backup_db.sh            # Бэкап БД с ротацией через pg_dump + gzip
│   └── migrate_old_posts.py    # Миграция постов из старого Go-сайта
├── projects.yaml               # Список проектов на странице /about
├── pyproject.toml              # Метаданные и зависимости Python
├── uv.lock                     # Lock-файл зависимостей (uv)
├── Dockerfile                  # Продакшен-образ на базе python:3.14-slim + uv
├── docker-compose.yml          # Локальная разработка: только PostgreSQL
├── docker-compose.prod.yml     # Продакшен: app + PostgreSQL + healthcheck
├── .env.example                # Шаблон переменных окружения для разработки
├── .env.prod.example           # Шаблон для продакшена
└── .dockerignore               # Исключения из Docker-контекста
```

## Внешние зависимости и их роль

| Зависимость | Роль |
|-------------|------|
| **FastAPI** (`../app/main.py`, `app/routers/*`) | Веб-фреймворк, маршрутизация, dependency injection, валидация форм |
| **uvicorn** | ASGI-сервер; запускается напрямую в Docker-контейнере |
| **psycopg[binary,pool]** (`../app/database.py`, `app/queries/*`) | Драйвер PostgreSQL + пул соединений; raw SQL вместо ORM |
| **Jinja2** (`../app/templating.py`, `app/templates/*`) | Шаблонизация HTML на сервере |
| **markdown-it-py** + **mdit-py-plugins** (`../app/markdown_render.py`) | Парсинг markdown, плагин dollarmath для LaTeX-мath |
| **Pygments** (`../app/markdown_render.py`) | Синтаксическая подсветка блоков кода |
| **argon2-cffi** (`../app/auth.py`) | Хеширование паролей администратора |
| **itsdangerous** (`../app/auth.py`) | Подпись и валидация cookie-сессий |
| **pydantic-settings** (`../app/config.py`) | Загрузка конфигурации из `.env` и переменных окружения |
| **python-multipart** | Парсинг multipart/form-data (формы админки и загрузка файлов) |
| **PyYAML** (`../app/projects.py`) | Чтение `../projects.yaml` |
| **PostgreSQL** | Хранение постов, тегов, пользователей, full-text search-индексов |
| **Cloudflare Tunnel** (вне репозитория) | Обратный прокси для продакшена; приложение слушает только `127.0.0.1` |
| **CDN KaTeX / Font Awesome / devicon / shields.io** (внешние) | Рендеринг формул, иконки, бейджи в about |
