# 04 — Оценка качества кодовой базы

## Общая оценка

| Критерий | Оценка | Комментарий |
|---|---|---|
| Читаемость | ★★★★☆ | Код чистый, типизированный, хорошо структурированный; читается легко |
| Модульность | ★★★☆☆ | Слои выделены, но бизнес-логика в routes; `services/` пуст |
| Связность (cohesion) | ★★☆☆☆ | Route-хендлеры совмещают HTTP, бизнес-логику и рендеринг |
| DRY | ★★☆☆☆ | Массовое дублирование логики пагинации в `items.py` |
| KISS | ★★★★☆ | Решения простые, без over-engineering |
| SOLID | ★★★☆☆ | DI (D) соблюдён; SRP нарушен (routes делают всё); OCP/LSP неприменимы |
| Безопасность | ★★☆☆☆ | XSS в inline HTML, нет CSRF, cookie без `Secure`, CDN-зависимости |
| Тестовое покрытие | ★★☆☆☆ | 4 smoke-теста; нет тестов бизнес-логики, auth, CRUD |

---

## Соответствие стандартам и идиомам

### Положительные аспекты

- **Python 3.12+**: используются `str | None` (PEP 604), `Mapped`/`mapped_column` (SQLAlchemy 2.0), `async`/`await` последовательно
- **Типизация**: большинство функций имеют type hints; `mypy` сконфигурирован с `warn_return_any`, `disallow_incomplete_defs`
- **Async-first**: весь DB-слой асинхронный (`create_async_engine`, `AsyncSession`, `aiosqlite`)
- **Pydantic v2**: `model_validator(mode="before")`, `SettingsConfigDict` — современные идиомы
- **Pre-commit**: 6 групп hooks обеспечивают консистентность

### Нарушения идиом

- `datetime.utcnow()` в `app/models/user.py:30` — **deprecated** в Python 3.12+; следует использовать `datetime.now(timezone.utc)`
- `dict[str, Any]` вместо Pydantic-модели в `app/api/user.py:44,95` — теряется валидация и type safety
- Inline HTML через f-strings в `app/api/user.py:65-76, 80-86, 105-111, 117-123, 133-139, 145-151, 158-164, 168-174` — нарушение SSR-подхода; должно быть в шаблонах

---

## Технический долг и code smells

### 1. Массовое дублирование логики пагинации (DRY violation)

**Файл:** `app/api/items.py`

Логика построения query, подсчёта total, вычисления пагинации и формирования context-словаря **повторяется 3 раза** практически идентично:
- `list_items()` (строки 32-84) — ~53 строки
- `create_item()` (строки 112-162) — ~51 строка
- `delete_item()` (строки 260-310) — ~51 строка

Context-словарь содержит 13 полей и конструируется вручную каждый раз. Один и тот же блок вычисления `has_prev`, `has_next`, `start_item`, `end_item`, `page_range_start`, `page_range_end` копипастится.

**Решение:** выделить в `app/services/pagination.py` функцию `build_pagination_context()`.

### 2. Мёртвый код: `get_db` в `dependencies.py`

**Файл:** `app/api/dependencies.py:6`

```python
def get_db(request: Request) -> Any:
    return request.state.db
```

Эта функция читает `request.state.db`, но **ни один middleware не устанавливает** `request.state.db`. Реальный `get_db` импортируется из `app/core/database.py`. Функция в `dependencies.py` никогда не вызывается — мёртвый код, вводящий в заблуждение.

### 3. Inline HTML с XSS-уязвимостью

**Файл:** `app/api/user.py:65-76`

```python
email_html = f"""
    <div ...>
        <span class="text-gray-800">{user.email}</span>
        <button onclick="editField('email', '{user.email}')" ...>
    </div>
    """
```

`user.email` подставляется в HTML и JS-строку через f-string **без экранирования**. Если email содержит `'` или HTML-символы, это приведёт к XSS или broken HTML. Должно рендериться через Jinja2 (который автоэкранирует).

Аналогично — `str(e)` в error-html (строки 83, 148, 171) может содержать произвольный текст исключения.

### 4. Несоответствие шаблона и роутов

**Файл:** `app/templates/partials/auth_links.jinja2:3-5`

Ссылается на `url_for("auth_logout_redirect")` — такого route name **не существует**. Роут logout называется `auth_logout` (`app/api/auth.py:71`). Partial-шаблон сломан.

### 5. Двойное управление схемой БД

`app/core/database.py:46` — `init_db()` вызывает `Base.metadata.create_all()` при каждом старте.
`alembic/env.py` — настроены миграции, но `alembic/versions/` пуст.

Два механизма управления схемой работают параллельно. `create_all` не учитывает миграции и может маскировать проблемы. Для production следует использовать только Alembic.

### 6. `SECRET_KEY` с runtime-default

**Файл:** `app/core/config.py:18`

```python
SECRET_KEY: str = secrets.token_hex(32)
```

Если `.env` не содержит `SECRET_KEY`, при каждом запуске генерируется новый ключ. Это:
- Инвалидирует все JWT-сессии при рестарте
- Делает token-секреты непредсказуемыми между деплойами
- В CI используется хардкоженный `test-secret-key-for-ci-only-not-secure`

### 7. Cookie без `Secure`-флага

**Файл:** `app/core/users.py:11`

```python
cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600)
```

`fastapi-users` `CookieTransport` по умолчанию не ставит `Secure=True`. В production по HTTPS cookie всё равно передаётся, но при MITM-атаке с понижением до HTTP cookie утекает.

### 8. Отсутствие CSRF-защиты

HTMX-запросы (`POST`, `PUT`, `DELETE`) не защищены CSRF-токенами. Cookie-based auth + отсутствие CSRF = классическая CSRF-уязвимость.

### 9. `Optional` из `typing` вместо `| None`

**Файл:** `app/api/items.py:1,23`

```python
from typing import Optional
search: Optional[str] = Query(None)
```

При Python 3.12+ и `from __future__ import annotations` или нативных union types — следует использовать `str | None`. В остальном проекте используется `| None` — несогласованность.

### 10. `List` из `typing` вместо `list`

**Файл:** `app/models/user.py:3,32`

```python
from typing import List
items: Mapped[List["Item"]] = relationship(...)
```

Python 3.12+ поддерживает `list["Item"]` как generic — `from typing import List` избыточен.

### 11. Отсутствие `order_by` в list-запросах

**Файл:** `app/api/items.py:33`

```python
query = select(Item).where(Item.owner_id == user.id)
```

Нет `order_by` — порядок строк не детерминирован. Пагинация на неупорядоченном множестве даёт непредсказуемые результаты (дубли/пропуски при переходе страниц).

### 12. Незакрытый `engine` при shutdown

`app/main.py:27` — `lifespan()` не вызывает `await engine.dispose()` после `yield`. Соединения могут оставаться открытыми до GC.

---

## Оценка безопасности и надёжности

| Угроза | Статус | Файл |
|---|---|---|
| **XSS** | 🔴 Уязвим — inline HTML с f-strings без экранирования | `app/api/user.py:65,83,145,168` |
| **CSRF** | 🔴 Отсутствует защита | Все POST/PUT/DELETE роуты |
| **Cookie security** | 🟡 Нет `Secure`-флага | `app/core/users.py:11` |
| **SECRET_KEY** | 🟡 Runtime-random default; CI-хардкод | `app/core/config.py:18`, `ci.yml:49` |
| **SQL Injection** | 🟢 Параметризованные запросы через SQLAlchemy | Повсеместно |
| **Password hashing** | 🟢 Через `fastapi-users` (`PasswordHelper`) | `app/models/user.py`, `app/api/user.py` |
| **Auth on routes** | 🟢 Все protected-роуты используют `current_user(active=True)` | `app/api/items.py`, `app/api/user.py` |
| **Owner isolation** | 🟢 Все Item-запросы фильтруют по `owner_id == user.id` | `app/api/items.py` |
| **Input validation** | 🟡 Items — Pydantic; User profile — `dict[str, Any]` без валидации | `app/api/user.py:44,95` |
| **Resource leaks** | 🟡 Engine не dispose при shutdown | `app/main.py:27` |
| **CDN dependencies** | 🟡 TailwindCSS Play CDN, HTMX CDN — недоступны при offline/SRI | `app/templates/base.jinja2:14-16` |
| **Rate limiting** | 🔴 Отсутствует | — |
| **CORS** | 🟡 Не настроен (может быть намеренно для SSR) | — |
