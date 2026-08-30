# Анализ потребления памяти и варианты оптимизации

## 1. Текущая архитектура загрузки контента

### 1.1. Точка запуска

При запуске сервера FastAPI вызывает функцию `lifespan`, которая загружает **весь** контент единовременно:

```python
# app/views/routes.py, строки 19–23
@asynccontextmanager
async def lifespan(_: FastAPI):
    get_content()          # ← HTML-контент: весь словарь
    get_ansi_content()     # ← ANSI-контент: весь словарь
    yield
```

Эта функция вызывается **один раз** за время жизни процесса. После завершения `lifespan` сервер готов принимать запросы.

### 1.2. Кэширование

Обе функции декорированы `@cache` (`functools.cache`):

```python
# app/services/html.py
@cache
def get_content():
    data = {
        "metadata": get_metadata_content(),
        "author": get_author_content(),
        "posts": get_posts_content(),
        "projects": get_projects_content(),
    }
    data["homepage"] = get_homepage_data(data["posts"], data["projects"])
    return data

# app/services/ansi.py
@cache
def get_ansi_content() -> ANSIContent:
    return {"posts": get_posts_content(), "projects": get_projects_content()}
```

`functools.cache` — это просто обёртка над `dict`. Результат вычисляется один раз, сохраняется в памяти и возвращается по ссылке. Объекты **никогда не удаляются** из кэша до перезапуска процесса.

### 1.3. Что именно загружается

`get_content()` последовательно вызывает:

```
get_content()
    ├── get_metadata_content()        # content/meta.md → MetadataMD
    ├── get_author_content()          # content/author/index.md → AuthorMD + фото
    ├── get_posts_content()           # content/posts/<slug>/index.md → dict[slug, PublishedContent]
    ├── get_projects_content()        # content/projects/<slug>/index.md → dict[slug, PublishedContent]
    └── get_homepage_data()           # content/homepage.md + вычисления
```

Для каждого поста/проекта выполняется полный конвейер:

```
content/posts/my-post/index.md
    ↓
get_content_context(path) → ContentContext
    ↓
move_image(context) → копирование images/ → app/static/images/posts/my-post/
    ↓
load_markdown_content() → MarkdownContent (Pydantic-модель)
    ↓
_parse_markdown(body) → HTML (markdown + BeautifulSoup + Tailwind-классы)
    ↓
get_headers_and_thumbnails(title) → выбор cover_NNN.png
    ↓
estimate_reading_time(body) → int
    ↓
PublishedContent → модель для шаблона
    ↓
posts[slug] = content.model_dump() → Python dict
```

### 1.4. Полная картина

```
lifespan()
    ├── get_content()     → dict["metadata", "author", "posts", "projects", "homepage"]
    │                       все body, все обложки, всё в памяти навсегда
    │
    └── get_ansi_content() → dict["posts", "projects"]
                            ещё одна полная копия всех body, ещё одна копия
```

---

## 2. Оценка потребления памяти

### 2.1. Структура данных одного поста

После `_get_published_content()` каждый пост сохраняется как словарь:

```python
# app/services/html.py, строка 268
posts[content.slug] = content.model_dump()
```

`model_dump()` превращает Pydantic-модель `PublishedContent` в обычный Python `dict`. Размер одного элемента:

| Поле | Тип | Ориентировочный размер |
|------|-----|------------------------|
| `slug` | `str` | 20–60 B |
| `title` | `str` | 20–100 B |
| `body` | `str \| None` | 5 000–50 000 B |
| `description` | `str \| None` | 100–300 B |
| `topic` | `str \| None` | 0–50 B |
| `repository` | `HttpUrl \| None` | 0–200 B |
| `website` | `HttpUrl \| None` | 0–200 B |
| `thumbnail_path` | `Path` | ~80 B |
| `cover_image_path` | `Path` | ~80 B |
| `reading_time_minutes` | `int` | 28 B |
| `publish_date` | `str` | 10–15 B |
| `extras` | `TemplateArgsDict` | ~50 B |
| **Служебные данные** (ссылки на объекты, хеши dict, внутренние структуры Python) | — | ~200–500 B |
| **Итого на один пост** | | **~6 000 – 100 000 B** |

### 2.2. Формула расчёта

```
память = N_postов × размер_поста + N_проектов × размер_проекта + базовые_структуры
```

Где:
- `размер_поста` ≈ `len(body_html) + 1 000` (тело + метаданные)
- `размер_проекта` ≈ `len(body_html) + 1 000`
- `базовые_структуры` ≈ 50 KB (словари, списки, служебные объекты)

### 2.3. Таблицы сценариев

#### Сценарий 1: Короткие посты (по 3 000 B HTML)

| Кол-во постов | Память (только посты) | Память (posts + projects) |
|---------------|----------------------|---------------------------|
| 10 | 30 KB | 150 KB |
| 50 | 150 KB | 750 KB |
| 100 | 300 KB | 1.5 MB |
| 500 | 1.5 MB | 7.5 MB |
| 1 000 | 3 MB | 15 MB |
| 5 000 | 15 MB | 75 MB |
| 10 000 | 30 MB | 150 MB |

#### Сценарий 2: Средние посты (по 10 000 B HTML)

| Кол-во постов | Память (только посты) | Память (posts + projects) |
|---------------|----------------------|---------------------------|
| 10 | 100 KB | 500 KB |
| 50 | 500 KB | 2.5 MB |
| 100 | 1 MB | 5 MB |
| 500 | 5 MB | 25 MB |
| 1 000 | 10 MB | 50 MB |
| 5 000 | 50 MB | 250 MB |
| 10 000 | 100 MB | 500 MB |

#### Сценарий 3: Длинные посты (по 50 000 B HTML)

| Кол-во постов | Память (только посты) | Память (posts + projects) |
|---------------|----------------------|---------------------------|
| 10 | 500 KB | 2.5 MB |
| 50 | 2.5 MB | 12.5 MB |
| 100 | 5 MB | 25 MB |
| 500 | 25 MB | 125 MB |
| 1 000 | 50 MB | 250 MB |
| 5 000 | 250 MB | 1.25 GB |
| 10 000 | 500 MB | 2.5 GB |

### 2.4. Проблема дублирования

Существует **две независимые копии** всех постов и проектов:

```
get_content()  →  dict["posts"][slug] = { "body": "HTML...", ... }
                                      ↓  ~10 KB на пост

get_ansi_content()  →  dict["posts"][slug] = { "body": "ANSI...", ... }
                                       ↓  ~10 KB на пост
```

Итого удвоенное потребление. Для 1 000 постов по 10 KB:

| Копия | Память |
|-------|--------|
| HTML (get_content) | ~10 MB |
| ANSI (get_ansi_content) | ~10 MB |
| **Итого** | **~20 MB** |

Кроме того, `get_content()` вызывается в **каждом маршруте**:

```python
# app/views/routes.py
def post_html_detail(request: Request, slug: str):
    content = get_content()   # ← вызывается при каждом запросе
    post = content["posts"].get(slug)
    ...

def home(request: Request):
    content = get_content()   # ← вызывается при каждом запросе
    ...
```

`@cache` гарантирует, что вычисление происходит только один раз, но каждый вызов — это lookup в `dict`. Это не проблема производительности (O(1)), но код выглядит как будто данные загружаются при каждом запросе.

---

## 3. Когда станет проблемой

### 3.1. Пороги

| Размер контента | Память | Вердикт |
|-----------------|--------|---------|
| Блог, 10–100 постов | 1–10 MB | ✅ Нет проблем |
| Портфолио, 10–50 проектов | 1–5 MB | ✅ Нет проблем |
| Документация, 500–1 000 страниц | 10–50 MB | ⚠️ Заметно, но терпимо |
| Wiki, 5 000+ страниц | 50–500 MB | ❌ Проблема |
| Огромная база знаний, 50 000+ страниц | 500 MB – 5 GB | ❌ Критично |

### 3.2. Дополнительные факторы

| Фактор | Влияние |
|--------|---------|
| Несколько процессов (workers) | × N workers |
| ANSI-контент | × 2 (уже заложено) |
| Hot reload в dev-режиме | Память растёт при каждом изменении файла |
| Длинный uptime (месяцы) | Утечки памяти Python-интерпретатора |
| 32-битная архитектура | Лимит ~4 GB на процесс |

---

## 4. Варианты оптимизации

### Вариант 1: Ленивая загрузка (по запросу)

**Суть:** Не загружать ничего при старте. Читать файл только когда запросили конкретный slug.

**Реализация:**

```python
# app/services/html.py
def get_post_by_slug(slug: str) -> dict:
    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = _load_and_parse_post(post_path)
        if content.slug == slug:
            return content.model_dump()
    raise HTTPException(status.HTTP_404_NOT_FOUND)

def get_project_by_slug(slug: str) -> dict:
    for project_path in PROJECTS_CONTENT_DIR.glob("*/index.md"):
        content = _load_and_parse_project(project_path)
        if content.slug == slug:
            return content.model_dump()
    raise HTTPException(status.HTTP_404_NOT_FOUND)
```

```python
# app/views/routes.py
def post_html_detail(request: Request, slug: str):
    post = get_post_by_slug(slug)
    metadata = get_metadata_content()  # маленькая, можно кэшировать
    author = get_author_content()      # маленькая, можно кэшировать
    context = {"metadata": metadata, "author": author, "post": post}
    return templates.TemplateResponse(request, "post_detail.html", context=context)
```

**Плюсы:**
- Память не зависит от количества файлов
- Минимальные изменения в архитектуре
- Данные всегда актуальны (нет кэша)

**Минусы:**
- Медленнее при первом запросе каждого поста (чтение + парсинг файла)
- Нет единой точки загрузки (сложнее отслеживать ошибки при старте)
- При большом количестве файлов `glob()` медленнее, чем lookup в `dict`

**Оценка:** Для 10 000 постов — каждый запрос нового поста = 50–200 ms задержки на парсинг.

---

### Вариант 2: Индекс + ленивая загрузка (рекомендуемый)

**Суть:** При старте загружать в память только **индексы** (slug, title, date, description). Тело поста (`body`) читать по запросу.

**Реализация:**

```python
# app/schemas.py — новая модель для индекса
class PostIndex(BaseModel):
    slug: str
    title: str
    description: str | None = None
    publish_date: str
    topic: str | None = None
    reading_time: str

# app/services/html.py
@cache
def get_post_index() -> list[PostIndex]:
    indices = []
    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = load_markdown_content(post_path)
        reading_time = estimate_reading_time(content.body)
        indices.append(PostIndex(
            slug=content.slug or get_slug(post_path),
            title=content.title,
            description=content.description,
            publish_date=content.date or get_creation_date(post_path),
            topic=content.topic,
            reading_time=f"{reading_time} min",
        ))
    return indices

@cache
def get_post_detail(slug: str) -> dict:
    """Загружает полный пост по slug. Читает файл с диска."""
    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = load_markdown_content(post_path)
        if content.slug == slug:
            content_context = get_content_context(post_path)
            parsed = _parse_markdown(content_context, content.body)
            headers_and_thumbnails = get_headers_and_thumbnails(content.title)
            return {
                "slug": content.slug,
                "title": content.title,
                "body": parsed["content"],
                "description": content.description,
                "publish_date": content.date,
                "topic": content.topic,
                "cover_image": headers_and_thumbnails["headers"].default_url,
                "thumbnail": headers_and_thumbnails["thumbnails"].default_url,
                "reading_time": f"{estimate_reading_time(content.body)} min",
                "extras": parsed["extras"],
            }
    raise HTTPException(status.HTTP_404_NOT_FOUND)
```

```python
# app/views/routes.py
@router.get("/p", response_class=HTMLResponse)
async def post_list(request: Request):
    indices = get_post_index()  # ← из кэша, быстро
    context = {
        "metadata": get_metadata_content(),
        "posts": indices,
    }
    return templates.TemplateResponse(request, "post_list.html", context)

@router.get("/p/{slug}", response_class=HTMLResponse)
async def post_detail(request: Request, slug: str):
    post = get_post_detail(slug)  # ← чтение с диска, один файл
    context = {
        "metadata": get_metadata_content(),
        "author": get_author_content(),
        "post": post,
    }
    return templates.TemplateResponse(request, "post_detail.html", context)
```

**Плюсы:**
- Индекс занимает минимум памяти (без body): ~500 B на пост
- 10 000 постов в индексе = ~5 MB вместо ~100 MB
- Быстрая отдача списков (из кэша)
- Тело читается только когда нужно
- Простая миграция от текущей архитектуры

**Минусы:**
- При запросе детальной страницы — задержка на чтение файла (5–50 ms)
- Сложнее отслеживать ошибки при старте (неизвестно, если файл битый, узнаем при первом запросе)
- Нужно кэшировать и индекс, и детальную страницу (если один пост смотрят много раз)

**Оценка памяти для 10 000 постов по 10 KB:**

| Компонент | Память |
|-----------|--------|
| Индексы (без body) | ~5 MB |
| Metadata + author | ~10 KB |
| Один детальный пост (при запросе) | ~10 MB |
| **Итого** | **~15 MB** вместо ~200 MB |

---

### Вариант 3: SQLite-хранилище

**Суть:** При старте прочитать все файлы и записать в локальную SQLite-базу. При запросе — SQL-запрос.

**Реализация:**

```python
# app/db.py
import sqlite3
from pathlib import Path

DB_PATH = Path("data/content.db")

def init_db():
    """Создаёт таблицу и заполняет данными из content/."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            slug TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            body TEXT NOT NULL,
            publish_date TEXT,
            topic TEXT,
            reading_time_minutes INTEGER
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(publish_date)")

    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = load_markdown_content(post_path)
        body_html = _parse_markdown_body(content.body)
        reading_time = estimate_reading_time(content.body)

        conn.execute(
            """INSERT OR REPLACE INTO posts
               (slug, title, description, body, publish_date, topic, reading_time_minutes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                content.slug or get_slug(post_path),
                content.title,
                content.description,
                body_html,
                content.date,
                content.topic,
                reading_time,
            ),
        )
    conn.commit()
    conn.close()

def get_post_by_slug(slug: str) -> dict | None:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT * FROM posts WHERE slug = ?", (slug,)
    ).fetchone()
    conn.close()
    if row:
        return dict(zip(["slug", "title", "description", "body",
                         "publish_date", "topic", "reading_time_minutes"], row))
    return None

def get_all_post_slugs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT slug, title, description, publish_date, topic, reading_time_minutes FROM posts"
    ).fetchall()
    conn.close()
    return [dict(zip(["slug", "title", "description", "publish_date",
                      "topic", "reading_time_minutes"], row)) for row in rows]
```

```python
# app/views/routes.py
from app.db import get_post_by_slug, get_all_post_slugs

@router.get("/p", response_class=HTMLResponse)
async def post_list(request: Request):
    posts = get_all_post_slugs()
    context = {"metadata": get_metadata_content(), "posts": posts}
    return templates.TemplateResponse(request, "post_list.html", context)

@router.get("/p/{slug}", response_class=HTMLResponse)
async def post_detail(request: Request, slug: str):
    post = get_post_by_slug(slug)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    context = {
        "metadata": get_metadata_content(),
        "author": get_author_content(),
        "post": post,
    }
    return templates.TemplateResponse(request, "post_detail.html", context)
```

**Плюсы:**
- Минимальная память (SQLite работает с файлом на диске)
- Быстрый поиск по slug, дате, topic
- Поддержка SQL-запросов (фильтрация, поиск, пагинация)
- Данные отделены от кода приложения
- Можно делать полнотекстовый поиск (FTS5)

**Минусы:**
- Нужна миграция (перенос данных из файлов в БД)
- Усложнение архитектуры (добавляется слой БД)
- При изменении файлов контента нужно перегенерировать БД
- Нужно обрабатывать race conditions при записи (одновременно lifespan + запросы)

**Оценка памяти для 10 000 постов по 10 KB:**

| Компонент | Память |
|-----------|--------|
| SQLite (файл на диске) | 0 (работает с диском) |
| metadata + author | ~10 KB |
| Один запрос (buffer) | ~10 MB (временно, освобождается) |
| **Итого** | **~10 MB** вместо ~100 MB |

---

### Вариант 4: Комбинированный (индекс в памяти + кэш деталей)

**Суть:** Гибридный подход. Индекс всегда в памяти (быстрый список), детальные страницы кэшируются с TTL.

**Реализация:**

```python
# app/services/html.py
from functools import cache
from time import time

# Вечный кэш индекса
@cache
def get_post_index() -> list[dict]:
    ...

# Кэш с TTL для деталей
_detail_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 300  # 5 минут

def get_post_detail(slug: str) -> dict | None:
    # Проверяем кэш
    if slug in _detail_cache:
        cached_time, cached_data = _detail_cache[slug]
        if time() - cached_time < CACHE_TTL:
            return cached_data

    # Читаем с диска
    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = load_markdown_content(post_path)
        if content.slug == slug:
            data = _build_post_detail(content, post_path)
            _detail_cache[slug] = (time(), data)
            return data
    return None

def clear_detail_cache():
    """Освобождает кэш деталей (вызывать при деплое новых файлов)."""
    _detail_cache.clear()
```

**Плюсы:**
- Индекс всегда быстрый
- Повторные запросы одного поста — мгновенно (из кэша)
- Кэш автоматически инвалидируется через TTL
- Можно добавить явную инвалидацию при деплое

**Минусы:**
- Сложнее код
- TTL — компромисс между свежестью и скоростью
- Нужен механизм инвалидации при изменении файлов

---

## 5. Сравнение вариантов

| Критерий | Вариант 1: Ленивая | Вариант 2: Индекс + ленивая | Вариант 3: SQLite | Вариант 4: Комбо |
|----------|-------------------|---------------------------|-------------------|------------------|
| Память (10K постов) | ~500 B на файл | ~5 MB | ~10 MB | ~5 MB |
| Скорость списка | O(N) сканирование | O(1) из кэша | O(1) из кэша | O(1) из кэша |
| Скорость детальной | 50–200 ms | 5–50 ms | 1–10 ms | 1–5 ms (кэш) |
| Сложность | Низкая | Средняя | Высокая | Высокая |
| Актуальность данных | Всегда | Всегда | При перегенерации | При перегенерации |
| Ошибки при старте | Нет | Нет | Да | Да |
| Поддержка поиска | Нет | Нет | Да (SQL) | Нет |
| Рекомендация | Для 10–100 постов | Для 500–5 000 постов | Для 5 000+ постов | Для 1 000+ постов |

---

## 6. Рекомендации

### Для текущего проекта (блог/портфолио)

**Оставить как есть.** 10–100 постов = 1–10 MB. Это ничтожно. Текущая архитектура — самая простая и надёжная.

### Если планируется рост до 500–1 000 страниц

**Внедрить Вариант 2 (индекс + ленивая загрузка).** Это минимальные изменения, максимальная отдача.

### Если планируется рост до 5 000+ страниц или нужна фильтрация/поиск

**Внедрить Вариант 3 (SQLite).** Это даст масштабирование и новые возможности поиска.

### Если нужно быстро и без миграции

**Вариант 4 (комбинированный).** Индекс в памяти, детали кэшируются с TTL. Не требует миграции данных.

---

## 7. Итог

| Ситуация | Текущий подход | При росте |
|----------|---------------|-----------|
| 10–100 постов | ✅ Оптимально | Остаётся оптимальным |
| 500–1 000 постов | ⚠️ Терпимо | Вариант 2 |
| 5 000+ постов | ❌ Проблематично | Вариант 3 |
| Нужен поиск/фильтрация | ❌ Невозможно | Вариант 3 (SQLite FTS) |
