# Отчёт: работа с базой данных в проекте `diegolonio.com`

## 1. План отчёта

1. Актуальное состояние работы с базой данных: используемые технологии, архитектура, модули, схема данных.
2. Постановка задачи: цель, область применения, ограничения.
3. Техническое задание на миграцию с текущего raw-SQL подхода на асинхронный SQLAlchemy 2.0 + Alembic.
4. Пошаговый план переделки: структура проекта, модели, сессии, миграции, репозитории, endpoint-ы, тестирование.
5. Риски, предостережения и рекомендации.

---

## 2. Актуальное состояние работы с базой данных

### 2.1. Используемый стек

| Компонент | Текущее решение | Назначение |
|-----------|-----------------|------------|
| СУБД | PostgreSQL 16 | Хранение данных блога |
| Драйвер | `psycopg[binary,pool]` | Синхронный драйвер + пул соединений |
| Пул | `psycopg_pool.ConnectionPool` | Управление соединениями (`min_size=1`, `max_size=10`) |
| SQL | Чистый raw SQL в `app/queries/` | CRUD, full-text search, пагинация |
| Миграции | SQL-скрипты в `migrations/` + `run_migrations.py` | Идемпотентный runner, таблица `schema_migrations` |

### 2.2. Конфигурация подключения

Подключение централизовано в `app/config.py` через `pydantic_settings.BaseSettings`:

```python
DATABASE_URL = "postgresql://diegolonio:diegolonio@localhost:5433/diegolonio"
```

Пул создаётся в `app/database.py` и открывается в `lifespan` приложения (`app/main.py`).

### 2.3. Схема базы данных

Текущая схема описана в `migrations/001_initial.sql`:

- `users` — администраторы (`id`, `username`, `password_hash`).
- `posts` — публикации (`id`, `slug`, `title`, `summary`, `cover_image`, `content_md`, `content_html`, `published`, `created_at`, `updated_at`, `published_at`, `search_vector`).
- `tags` — теги (`id`, `name`, `slug`).
- `post_tags` — связь многие-ко-многим между постами и тегами.

Индексы:

- `posts_search_idx` — GIN по `search_vector` для full-text search.
- `posts_published_idx` — B-tree по `(published, published_at DESC)` для публичных списков.

### 2.4. Архитектура доступа к данным

```
FastAPI endpoint
    └── Depends(get_db)
            └── app/database.py::get_db()
                    └── pool.connection() as conn
                            └── app/queries/{posts,tags,users}.py
                                    └── raw SQL
```

Модули `app/queries/` выполняют роль лёгкого Repository / Table Data Gateway:

- `app/queries/posts.py` — 13 функций: CRUD постов, пагинация, поиск, slug, теги.
- `app/queries/tags.py` — 5 функций: CRUD тегов, связь `post_tags`.
- `app/queries/users.py` — 2 функции: получение и upsert пользователя.

### 2.5. Примеры ключевых SQL-конструкций

**Full-text search** (`app/queries/posts.py::search`):

```sql
SELECT p.id, p.slug, p.title, p.summary, p.cover_image, p.published_at
FROM posts p
CROSS JOIN LATERAL websearch_to_tsquery('english', %s) AS q
WHERE p.published AND p.search_vector @@ q
ORDER BY ts_rank(p.search_vector, q) DESC, p.published_at DESC
LIMIT %s
```

**Генерация `published_at` только при первой публикации** (`posts.create`, `posts.update`, `posts.set_published`):

```sql
published_at = CASE
    WHEN %s AND published_at IS NULL THEN now()
    ELSE published_at
END
```

### 2.6. Миграции

Миграции хранятся как последовательные SQL-файлы:

```
migrations/
├── 001_initial.sql
└── run_migrations.py
```

Runner создаёт таблицу `schema_migrations`, считывает применённые файлы и применяет только новые. Это простое и рабочее решение, но не поддерживает:

- откат миграций (downgrade);
- автогенерацию по изменениям моделей;
- проверку зависимостей и конфликтов;
- версионирование в командах CLI.

---

## 3. Постановка задачи

### 3.1. Цель

Разработать техническое задание по переводу слоя работы с базой данных проекта `diegolonio.com` с синхронного raw SQL (`psycopg_pool` + ручные SQL-запросы) на асинхронный стек **SQLAlchemy 2.0 + asyncpg + Alembic**, сохранив существующую бизнес-логику, схему данных и философию проекта.

### 3.2. Обоснование

| Проблема текущего подхода | Как решит SQLAlchemy + Alembic |
|---------------------------|--------------------------------|
| Синхронный пул блокирует event loop uvicorn на время запросов к БД | Асинхронный `AsyncSession` через `asyncpg` не блокирует loop |
| SQL-запросы разбросаны по модулям, нет единой схемы в коде | Declarative модели централизуют структуру таблиц |
| Миграции вручную, риск ошибок при изменении схемы | Alembic генерирует и версионирует миграции |
| Сложнее писать unit- и интеграционные тесты | ORM-сессии проще подменять и сбрасывать |
| Рост связности между роутерами и SQL | Репозитории/сервисы с чёткими интерфейсами |

### 3.3. Ограничения и требования

- Сохранить PostgreSQL как единственную СУБД.
- Сохранить существующую схему таблиц (`users`, `posts`, `tags`, `post_tags`), индексы и full-text search.
- Сохранить поведение `published_at` (устанавливается только при первой публикации).
- Сохранить server-side Jinja2 рендеринг и структуру роутеров.
- Не внедрять тяжёлый фронтенд, CMS или ORM-зависимую бизнес-логику.
- Поддержать `Python >= 3.14` и `uv` для управления зависимостями.

---

## 4. Техническое задание

### 4.1. Целевой стек

| Компонент | Библиотека | Версия (ориентировочно) |
|-----------|------------|-------------------------|
| ORM | SQLAlchemy | `>=2.0.40` |
| Асинхронный драйвер | asyncpg | `>=0.30.0` |
| Миграции | Alembic | `>=1.15.0` |
| Валидация данных | Pydantic | встроен в FastAPI / pydantic-settings |
| Интеграция с FastAPI | `AsyncSession` + `Depends` | — |

### 4.2. Структура проекта после миграции

```
app/
├── main.py                  # lifespan: engine.dispose(), routers
├── config.py                # DATABASE_URL_ASYNC, ECHO_SQL
├── database.py              # async engine + async_sessionmaker + get_db
├── models/
│   ├── __init__.py          # экспорт Base и моделей
│   ├── base.py              # declarative_base()
│   ├── user.py              # User
│   ├── post.py              # Post
│   ├── tag.py               # Tag
│   └── post_tag.py          # post_tags association
├── repositories/
│   ├── __init__.py
│   ├── posts.py             # PostRepository (async)
│   ├── tags.py              # TagRepository (async)
│   └── users.py             # UserRepository (async)
├── schemas/                 # Pydantic-схемы для входа/выхода и валидации форм
├── routers/
│   ├── public.py            # async endpoint-ы
│   └── admin.py             # async endpoint-ы
└── ...
migrations/
└── versions/                # Alembic: autogenerated .py файлы
alembic.ini                  # конфигурация Alembic
pyproject.toml               # + sqlalchemy[asyncpg], alembic
```

### 4.3. Конфигурация

В `app/config.py` добавить:

```python
database_url_async: str = "postgresql+asyncpg://diegolonio:diegolonio@localhost:5433/diegolonio"
echo_sql: bool = False
```

### 4.4. Движок и сессии

Файл `app/database.py`:

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

engine = create_async_engine(
    settings.database_url_async,
    echo=settings.echo_sql,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 4.5. Модели SQLAlchemy

Файл `app/models/post.py` (пример):

```python
from datetime import datetime
from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    Index,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_image: Mapped[str | None] = mapped_column(String, nullable=True)
    content_md: Mapped[str] = mapped_column(Text, nullable=False, default="")
    content_html: Mapped[str] = mapped_column(Text, nullable=False, default="")
    published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    search_vector = mapped_column(
        # Сохраняем существующий GENERATED ALWAYS вручную через DDL или Alembic
    )

    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=post_tags, back_populates="posts"
    )

    __table_args__ = (
        Index("posts_search_idx", "search_vector", postgresql_using="gin"),
        Index("posts_published_idx", "published", "published_at"),
    )
```

> **Важно:** `search_vector` должен остаться `GENERATED ALWAYS ... STORED` на стороне PostgreSQL. SQLAlchemy 2.0 не поддерживает generated tsvector напрямую в `mapped_column`; рекомендуется:
> - создать колонку через `Computed(..., persisted=True)` с кастомным выражением;
> - либо оставить управление `search_vector` на уровне Alembic-миграций (ручной DDL), а в модели пометить как `deferred` / `server_default=text("...")`.

### 4.6. Pydantic-схемы

Ввести явные схемы для валидации форм, API и сериализации в шаблоны:

```python
# app/schemas/posts.py
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    slug: str | None = Field(None, max_length=300)
    summary: str = Field(default="", max_length=2000)
    cover_image: str | None = Field(None, max_length=500)
    content_md: str = Field(default="", max_length=500_000)
    published: bool = False
    tags: str = Field(default="", max_length=1000)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    summary: str
    cover_image: str | None
    content_html: str
    published: bool
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
```

Аналогично создать `app/schemas/tags.py` и `app/schemas/users.py`. Роутеры используют схемы для валидации `Form(...)` и приведения ORM-объектов к plain dict перед рендерингом Jinja2.

### 4.7. Репозитории

Переписать `app/queries/` на асинхронные репозитории, используя только SQLAlchemy 2.0 Core/ORM:

```python
# app/repositories/posts.py
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.post import Post


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_published(self, limit: int, offset: int):
        stmt = (
            select(Post.id, Post.slug, Post.title, Post.summary, Post.cover_image, Post.published_at)
            .where(Post.published.is_(True))
            .order_by(Post.published_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.mappings().all()

    async def count_published(self) -> int:
        stmt = select(func.count(Post.id)).where(Post.published.is_(True))
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def search(self, query: str, limit: int = 50):
        # Реализовать через SQLAlchemy Core с tsvector_rank и to_tsquery,
        # либо через PostgreSQL-специфичные функции, обёрнутые в sqlalchemy.func.
        ...
```

> **Full-text search** должен быть реализован без raw SQL. Варианты:
> - обернуть `websearch_to_tsquery`, `ts_rank`, `to_tsvector` через `sqlalchemy.func`;
> - использовать `sqlalchemy.dialects.postgresql.TSVECTOR`, `TSQUERY` и `match` оператор `@` через `sqlalchemyOperators`;
> - при необходимости вынести поисковую логику в отдельный Query Object (`app/repositories/queries/post_search.py`), но всё равно на SQLAlchemy Core.

### 4.7. Роутеры

Все endpoint-функции становятся `async` и используют `AsyncSession`:

```python
# app/routers/public.py
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.posts import PostRepository

router = APIRouter()

@router.get("/")
async def home(request: Request, db: AsyncSession = Depends(get_db)):
    repo = PostRepository(db)
    posts = await repo.list_published(limit=6, offset=0)
    total = await repo.count_published()
    ...
```

### 4.8. Миграции Alembic

#### 4.8.1. Инициализация

```bash
uv add "sqlalchemy[asyncpg]>=2.0.40" alembic>=1.15.0
uv run alembic init alembic
```

Перенести Alembic-конфиг в `migrations/` или оставить в корне — по договорённости команды. Рекомендуется:

```
migrations/
├── env.py
├── script.py.mako
├── versions/
└── alembic.ini  # или в корне
```

#### 4.8.2. Конфигурация `alembic.ini`

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
sqlalchemy.url = postgresql+asyncpg://diegolonio:diegolonio@localhost:5433/diegolonio
```

#### 4.8.3. `migrations/env.py`

- Использовать `AsyncEngine` и `run_async` / `run_migrations_online`.
- Импортировать `Base` из `app.models.base`.
- Установить `target_metadata = Base.metadata`.
- Для асинхронного движка использовать `async with connectable.connect() as connection:` + `await connection.run_sync(do_run_migrations)`.

#### 4.8.4. Первая миграция

Создать начальную миграцию, идентичную существующей схеме:

```bash
uv run alembic revision --autogenerate -m "initial_schema"
```

После автогенерации вручную проверить и скорректировать:

- `search_vector` — должен быть `GENERATED ALWAYS AS (... ) STORED`.
- GIN-индекс `posts_search_idx`.
- Композитный первичный ключ `post_tags`.
- `ON DELETE CASCADE` для внешних ключей.

#### 4.8.5. Дальнейшие изменения

После изменения моделей:

```bash
uv run alembic revision --autogenerate -m "add_user_avatar"
uv run alembic upgrade head
uv run alembic downgrade -1
```

### 4.9. Тестирование

| Уровень | Подход |
|---------|--------|
| Unit | pytest + `AsyncMock` для репозиториев |
| Integration | `pytest-asyncio` + testcontainers PostgreSQL + `AsyncSession` |
| E2E | `httpx.AsyncClient` + `async ASGITransport` |

Пример фикстуры:

```python
# tests/conftest.py
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

TEST_DB_URL = "postgresql+asyncpg://test:test@localhost:5433/test"

@pytest_asyncio.fixture
async def db():
    engine = create_async_engine(TEST_DB_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()
```

### 4.10. Запуск и проверка

```bash
# 1. Поднять БД
docker compose up -d

# 2. Применить миграции
uv run alembic upgrade head

# 3. Создать администратора
uv run python scripts/create_admin.py

# 4. Запустить приложение
uv run uvicorn app.main:app --reload
```

---

## 5. Пошаговый план переделки

| Этап | Задача | Результат |
|------|--------|-----------|
| 1 | Добавить зависимости | `pyproject.toml` + `uv.lock` |
| 2 | Настроить Alembic | `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako` |
| 3 | Создать модели SQLAlchemy | `app/models/` |
| 4 | Переписать `app/database.py` на async | `AsyncEngine`, `AsyncSession`, `get_db` |
| 5 | Создать Pydantic-схемы | `app/schemas/` |
| 6 | Создать асинхронные репозитории | `app/repositories/` |
| 7 | Переписать роутеры на `async` + `AsyncSession` + Pydantic | `app/routers/public.py`, `app/routers/admin.py` |
| 8 | Обновить вспомогательные модули | `app/slugs.py`, `app/media_cleanup.py`, `scripts/*.py` |
| 9 | Сгенерировать начальную Alembic-миграцию | `migrations/versions/001_initial_schema.py` |
| 10 | Удалить старые SQL-миграции | `migrations/001_initial.sql`, `run_migrations.py` (или архивировать) |
| 11 | Написать тесты | `tests/` |
| 12 | Проверить вручную | create, read, update, publish, delete, search, tags, login |
| 13 | Обновить документацию | `README.md`, `docs/*.md` |

---

## 6. Риски и предостережения

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Потеря full-text search производительности | Средняя | Высокое | Оставить `search_vector` как generated column + GIN индекс вручную |
| Различия в поведении `published_at` | Средняя | Среднее | Вынести логику в триггер БД или явно управлять в сервисном слое |
| Проблемы с `asyncpg` и `uuid`/JSON | Низкая | Среднее | Тщательное тестирование типов |
| Неправильная автогенерация индексов Alembic | Средняя | Среднее | Ручная правка миграций |
| Усложнение небольшого проекта | Высокая | Среднее | Сохранять простые репозитории, не вводить избыточные абстракции |
| Падение производительности из-за lazy loading | Средняя | Среднее | Использовать `selectinload`, `joinedload` явно; отключить lazy loading в тестах |
| Рост сложности full-text search на ORM | Средняя | Среднее | Вынести поиск в отдельный Query Object на SQLAlchemy Core; покрыть тестами эквивалентность поведения |

---

## 7. Рекомендации

1. **Не конвертировать SQLAlchemy-модели в Active Record**: сохранить Repository-паттерн, чтобы роутеры оставались тонкими.
2. **Исключить raw SQL из прикладного кода**: full-text search, CTE и аналитику выразить через SQLAlchemy 2.0 Core/ORM-конструкции. Raw SQL допускается только внутри Alembic-миграций и, в крайнем случае, в отдельном слое оптимизированных запросов с чётким обоснованием.
3. **Ввести Pydantic-схемы** для валидации входных данных и сериализации ответов: `app/schemas/posts.py`, `app/schemas/tags.py`, `app/schemas/users.py`.
4. **Ввести сервисный слой** одновременно с миграцией: `app/services/posts.py`, `app/services/tags.py`.
5. **Настроить `ruff` и `mypy`** для проверки типов SQLAlchemy 2.0.
6. **Использовать `expire_on_commit=False`** в `async_sessionmaker` для удобной работы с объектами после commit.
7. **Не удалять старые миграции сразу**: сохранить `migrations/001_initial.sql` в архив до полной проверки.
8. **Проверить резервное копирование**: `scripts/backup_db.sh` использует `pg_dump`, он остаётся актуальным.

---

## 8. Итог

Проект `diegolonio.com` в настоящее время использует минималистичный, но рабочий подход на основе синхронного `psycopg_pool` и raw SQL. Переход на **асинхронный SQLAlchemy 2.0 + asyncpg + Alembic** повысит масштабируемость, упростит тестирование и автоматизирует управление схемой данных, сохранив при этом существующую бизнес-логику и философию проекта.

Ключевые моменты миграции:

- сохранить generated `search_vector` и GIN-индекс;
- сохранить поведение `published_at`;
- использовать Repository-паттерн поверх `AsyncSession`;
- весь прикладной код (включая full-text search) выразить через SQLAlchemy 2.0 Core/ORM без raw SQL;
- валидировать входные данные через Pydantic-схемы;
- вручную дорабатывать Alembic-миграции после автогенерации;
- обязательно покрыть тестами CRUD, поиск, теги и аутентификацию.
