# diegolonio.com

Персональный блог и портфолио Diego Villegas.

Минималистичное серверное веб-приложение на **FastAPI**, чистом **SQL** (psycopg 3), шаблонах **Jinja2** и со встроенным markdown-редактором. Без ORM, без frontend-фреймворков, без CMS.

## Документация

Документация проекта находится в папке `docs/`. Перед изучением кодовой базы читайте эти файлы по порядку:

1. [`docs/01_project_structure.md`](./docs/01_project_structure.md) — назначение проекта, дерево директорий, ключевые файлы и внешние зависимости.
2. [`docs/02_architecture.md`](./docs/02_architecture.md) — высокоуровневая архитектура, слои и паттерны.
3. [`docs/03_execution_flow.md`](./docs/03_execution_flow.md) — жизненный цикл приложения и ключевые бизнес-процессы.
4. [`docs/04_code_quality.md`](./docs/04_code_quality.md) — оценка качества кода и технический долг.
5. [`docs/05_optimization_roadmap.md`](./docs/05_optimization_roadmap.md) — дорожная карта и предложения по улучшению.

> **Примечание для AI-агентов:** Всегда сначала обращайтесь к документации в `docs/`. Избегайте лишнего обхода всего проекта — в документации уже содержится контекст, необходимый для большинства задач.

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните значения.
2. Запустите PostgreSQL локально:
   ```bash
   docker-compose up -d
   ```
3. Примените миграции:
   ```bash
   python migrations/run_migrations.py
   ```
4. Создайте администратора:
   ```bash
   python scripts/create_admin.py
   ```
5. Запустите приложение:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## Продакшен

1. Скопируйте `.env.prod.example` в `.env` и укажите продакшен-секреты.
2. Примените миграции.
3. Разверните через Docker Compose:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Стек технологий

- Python 3.14
- FastAPI + Uvicorn
- PostgreSQL
- Jinja2
- markdown-it-py + Pygments
- argon2-cffi + itsdangerous

## Лицензия

Приватный проект — все права защищены.
