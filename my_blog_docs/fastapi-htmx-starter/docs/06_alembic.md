# 06 — Alembic: миграции базы данных

## Назначение

[Alembic](https://alembic.sqlalchemy.org/) — инструмент управления миграциями схемы БД для SQLAlchemy. В проекте он обеспечивает версионированное изменение структуры БД (создание/изменение таблиц, индексов и т.д.) без ручного SQL.

Проект использует **асинхронный** режим Alembic (`async_engine_from_config` + `aiosqlite`/`asyncpg`), что соответствует async-архитектуре SQLAlchemy 2.0.

---

## Структура файлов

```
alembic/
├── env.py                # Конфигурация окружения миграций (async-движок, target_metadata)
├── script.py.mako        # Mako-шаблон для генерации файлов миграций
├── README                # Стандартный Alembic README
└── versions/             # Директория для файлов миграций (*.py)
alembic.ini               # Конфигурация Alembic: script_location, sqlalchemy.url, логгеры
```

---

## Конфигурация

### `alembic.ini`

| Параметр | Значение | Описание |
|---|---|---|
| `script_location` | `alembic` | Путь к директории с env.py и versions/ |
| `sqlalchemy.url` | `sqlite+aiosqlite:///./app.db` | URL БД по умолчанию (переопределяется в `env.py`) |
| `prepend_sys_path` | `.` | Корень проекта добавляется в `sys.path` (для импорта `app.*`) |
| `version_path_separator` | `os` | Разделитель путей (OS-зависимый) |

> **Важно:** значение `sqlalchemy.url` из `alembic.ini` **переопределяется** во время выполнения. В `env.py` URL берётся из `settings.DATABASE_URL` (Pydantic Settings, читает `.env`). Это означает, что реальная БД определяется переменной окружения `DATABASE_URL`, а не `alembic.ini`.

### `alembic/env.py`

Ключевые аспекты конфигурации:

1. **`target_metadata = Base.metadata`** — Alembic сравнивает состояние БД с метаданными SQLAlchemy-моделей (`app.core.database.Base`). Все модели должны быть импортированы (через цепочку импортов), чтобы попасть в `Base.metadata`.

2. **Offline-режим** (`run_migrations_offline`) — генерирует SQL-скрипт без подключения к БД. URL берётся из `settings.DATABASE_URL`.

3. **Online-режим** (`run_async_migrations` → `run_migrations_online`) — подключается к БД через `async_engine_from_config` с `NullPool` и применяет миграции. Запуск через `asyncio.run()`.

4. **Override URL** — строка `configuration["sqlalchemy.url"] = settings.DATABASE_URL` подменяет URL из `alembic.ini` на актуальный из настроек приложения.

---

## Команды

Все команды выполняются из корня проекта. Предполагается, что виртуальное окружение активировано.

### Создание миграции

```bash
# Автоматическая генерация на основе изменений моделей
alembic revision --autogenerate -m "Описание миграции"

# Пустая миграция (ручное написание upgrade/downgrade)
alembic revision -m "Описание миграции"
```

> **NB:** `--autogenerate` сравнивает `Base.metadata` с текущим состоянием БД. Перед запуском убедитесь, что БД соответствует последней миграции (`alembic upgrade head`). Autogenerate **не обнаруживает** все изменения (например, переименование столбца выглядит как drop + add).

### Применение миграций

```bash
# Применить все миграции до последней
alembic upgrade head

# Применить N следующих миграций
alembic upgrade +1

# Применить миграции до конкретной ревизии
alembic upgrade <revision_id>
```

### Откат миграций

```bash
# Откатить одну последнюю миграцию
alembic downgrade -1

# Откатить N миграций
alembic downgrade -3

# Откатить все миграции до базового состояния
alembic downgrade base

# Откатить до конкретной ревизии
alembic downgrade <revision_id>
```

### Просмотр состояния

```bash
# Текущая ревизия в БД
alembic current

# История всех миграций (новые → старые)
alembic history

# История с содержимым (verbose)
alembic history --verbose

# Список головных ревизий (полезно при ветвлении)
alembic heads
```

### Другие полезные команды

```bash
# Проверить, что все модели импортированы и видны Alembic
alembic check

# Сгенерировать SQL без применения (offline-режим)
alembic upgrade head --sql

# Подавить вывод логов
alembic upgrade head -q
```

---

## Типичный рабочий процесс

### 1. Изменение модели

Добавьте или измените SQLAlchemy-модель в `app/models/`. Убедитесь, что модель импортируется и попадает в `Base.metadata`.

### 2. Генерация миграции

```bash
alembic revision --autogenerate -m "Add new column to items"
```

Alembic создаст файл в `alembic/versions/` вида `<revision>_add_new_column_to_items.py`.

### 3. Проверка сгенерированной миграции

Откройте созданный файл и проверьте функции `upgrade()` и `downgrade()`. Autogenerate может:
- пропустить изменения, которые не умеет детектировать (переименования, check-констрейнты и т.д.);
- сгенерировать лишние операции, если БД и модели рассинхронизированы.

### 4. Применение

```bash
alembic upgrade head
```

### 5. Коммит

Закоммитьте файл миграции из `alembic/versions/` вместе с изменениями моделей.

---

## Важные замечания

### Дублирование с `create_all`

В проекте существует `init_db()` (`app/core/database.py:46`), который вызывает `Base.metadata.create_all`. Это создаёт таблицы напрямую, **минуя миграции**. В production следует использовать **только Alembic**. См. также [05_optimization_roadmap.md](05_optimization_roadmap.md).

### Пустая директория `versions/`

В шаблоне директория `alembic/versions/` пуста — первая миграция должна быть сгенерирована разработчиком при инициализации проекта:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Async-специфика

Поскольку проект использует async SQLAlchemy (`aiosqlite` / `asyncpg`), `env.py` написан в async-стиле:
- `run_migrations_online()` вызывает `asyncio.run(run_async_migrations())`;
- движок создаётся через `async_engine_from_config` с `pool.NullPool`;
- подключение выполняется через `async with connectable.connect()`, а миграции — через `connection.run_sync(do_run_migrations)`.

Это означает, что все команды `alembic` работают с async-драйверами без дополнительных флагов.

### Переключение на PostgreSQL

Для использования PostgreSQL вместо SQLite достаточно изменить `DATABASE_URL` в `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
```

Никаких изменений в `alembic.ini` или `env.py` не требуется — URL подставляется динамически из `settings.DATABASE_URL`.
