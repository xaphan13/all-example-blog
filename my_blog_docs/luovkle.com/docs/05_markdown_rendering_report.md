# Отчёт: как рендерится Markdown — сервер vs клиент

## 1. Краткий ответ

Markdown в проекте `luovkle.com` рендерится **полностью на сервере**. В браузер приходит уже готовый HTML (или ANSI-арт для CLI-клиентов). Никакого клиентского Markdown-рендерера (например, marked.js, remark, mdx) в репозитории нет.

---

## 2. Общая архитектура рендеринга

Приложение — монолитный серверно-рендеринговый сайт (SSR-like) на FastAPI. Контент хранится в Markdown-файлах в `content/`, преобразуется в Python-структуры при старте и отдаётся клиентам двумя способами:

| Клиент | Формат ответа | Технологии |
|--------|---------------|------------|
| Браузер | `text/html` | Python `markdown` + `BeautifulSoup` + Jinja2 + Tailwind CSS |
| CLI (`curl`, `httpie`, `wget`) | `text/plain` | Python `rich` (Markdown → ANSI) + Jinja2 ANSI-шаблоны |

```text
┌─────────────┐      HTTPS/HTTP      ┌─────────────┐      HTTP       ┌─────────────┐
│   Client    │ ───────────────────▶ │    Caddy    │ ──────────────▶ │  www:4000   │
│ curl/browser│ ◀─────────────────── │  (proxy+fs) │ ◀────────────── │   FastAPI   │
└─────────────┘                      └─────────────┘                 └─────────────┘
                                            │                               │
                                            ▼                               │
                                     /srv/static/* ◀────────────────────────┘
```

---

## 3. Серверный рендеринг HTML

### 3.1. Точка входа

Маршруты FastAPI в `app/views/routes.py` вызывают `get_content()` — кэшированную фабрику, которая загружает и преобразует весь Markdown-контент.

```python
# app/views/routes.py
@router.get("/p/{slug}", response_class=HTMLResponse)
async def post_detail(
    request: Request,
    slug: str,
    cli_client: Annotated[bool, Depends(is_cli_client)],
):
    if cli_client:
        return post_ansi_detail(slug)
    return post_html_detail(request, slug)


def post_html_detail(request: Request, slug: str):
    content = get_content()
    post = content["posts"].get(slug)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    context = {
        "metadata": content["metadata"],
        "author": content["author"],
        "post": post,
    }
    return templates.TemplateResponse(request, "post_detail.html", context=context)
```

### 3.2. Построение HTML-контекста

`app/services/html.py::get_content()` собирает данные:

```text
get_content()
    ├── get_metadata_content()      # content/meta.md → MetadataMD
    ├── get_author_content()        # content/author/index.md → AuthorMD + фото
    ├── get_posts_content()         # content/posts/* → dict[slug, PublishedContent]
    ├── get_projects_content()      # content/projects/* → dict[slug, PublishedContent]
    └── get_homepage_data()         # content/homepage.md + counts/thumbnails
```

Для каждого поста/проекта:

```text
get_content_objects(POSTS_CONTENT_DIR)
    → get_content_context(path)      # определяет index.md и images/
    → _get_published_content(ctx)
        ├── move_image(ctx)          # копирует images/ → app/static/images/<type>/<slug>/
        ├── load_markdown_content()  # YAML-фронтматтер + Markdown-тело
        ├── _parse_markdown(body)    # Markdown → HTML + постобработка
        ├── get_slug() / markdown_content.slug
        ├── get_headers_and_thumbnails(title)  # выбор cover_NNN.png
        ├── estimate_reading_time(body)
        └── get_creation_date() / markdown_content.date
```

### 3.3. Markdown → HTML

Ключевая функция `_parse_markdown()` в `app/services/html.py`:

```python
# app/services/html.py
def _parse_markdown(content_context: ContentContext, body: str) -> ParsedMarkdownDict:
    # 1. Markdown → HTML
    html_content = markdown.markdown(
        body,
        extensions=["fenced_code", "codehilite"],
        output_format="html",
    )
    template_args: TemplateArgsDict = {"code": False}

    # 2. Парсинг и постобработка HTML
    soup = BeautifulSoup(html_content, "html.parser")

    # 3. Перезапись локальных изображений
    imgs = soup.find_all("img")
    directory = content_context.index_file.parent
    for img in imgs:
        img_src_raw = img.get("src")
        img_src_str = str(img_src_raw)
        if not img_src_raw or _is_external_url(img_src_str):
            continue
        src_name = Path(img_src_str).name
        dest = IMAGES_DIR / content_context.content_type / directory.name / src_name
        rel = STATIC_PREFIX + str(dest.relative_to(STATIC_RELATIVE_DIR).as_posix())
        img["src"] = rel

    # 4. Проверка наличия блоков кода
    code_blocks = soup.find_all("code")
    if len(code_blocks) >= 1:
        template_args["code"] = True

    # 5. Навешивание Tailwind-классов
    for tag in soup.find_all("a"):
        tag.attrs["class"] = "text-sky-500 font-bold"
        tag.attrs["target"] = "_blank"
        tag.attrs["rel"] = "noopener noreferrer"

    for tag in soup.find_all("h1"):
        tag.attrs["class"] = "text-4xl font-black"

    for tag in soup.find_all("h2"):
        tag.attrs["class"] = "text-3xl font-black"

    for tag in soup.find_all("h3"):
        tag.attrs["class"] = "text-2xl font-black"

    for tag in soup.find_all("h4"):
        tag.attrs["class"] = "text-xl font-black"

    for tag in soup.find_all("h5"):
        tag.attrs["class"] = "text-xl font-bold"

    for tag in soup.find_all("h6"):
        tag.attrs["class"] = "text-lg font-bold"

    for tag in soup.find_all("blockquote"):
        tag.attrs["class"] = (
            "bg-neutral-900 px-4 py-2 italic rounded-md text-base font-medium"
        )

    for tag in soup.find_all("ul"):
        tag.attrs["class"] = "ps-5 space-y-1 list-disc list-inside"

    for tag in soup.find_all("ol"):
        tag.attrs["class"] = "ps-5 space-y-1 list-decimal list-inside"

    for tag in soup.find_all("img"):
        tag.attrs["class"] = "mx-auto"

    for tag in soup.find_all("pre"):
        tag.attrs["class"] = "py-3 px-3 text-md overflow-x-auto"

    return {"content": str(soup), "extras": template_args}
```

### 3.4. Используемые Python-зависимости

Из `pyproject.toml`:

```toml
dependencies = [
    "beautifulsoup4>=4.14.0",
    "fastapi[standard-no-fastapi-cloud-cli]>=0.139.0",
    "markdown>=3.9",
    "pygments>=2.19.2",
    "pyyaml>=6.0.3",
    "rich>=14.1.0",
]
```

| Зависимость | Роль |
|-------------|------|
| `markdown` | Преобразование Markdown-тел в HTML с расширениями `fenced_code` и `codehilite` |
| `Pygments` | Подсветка синтаксиса в блоках кода; генерация `highlight.css` |
| `beautifulsoup4` | Постобработка HTML: перезапись `src` изображений, навешивание Tailwind-классов, поиск `<code>` |
| `PyYAML` | Парсинг YAML-фронтматтера |

### 3.5. Вставка HTML в шаблон

В Jinja2-шаблоне `app/templates/post_detail.html` тело поста вставляется как безопасный HTML:

```jinja2
{% if post.body %}
  <div class="text-lg space-y-10">{{ post.body|safe }}</div>
{% endif %}
```

Фильтр `|safe` говорит Jinja2, что строка уже содержит HTML и её не нужно экранировать.

### 3.6. Подсветка синтаксиса

Если в Markdown есть блоки кода (`<code>`), в `extras.code` устанавливается `True`, и в шаблон лениво подгружается `highlight.css`:

```jinja2
{% if post.extras.code %}
  <link rel="preload"
        as="style"
        onload="this.onload=null;this.rel='stylesheet'"
        href="{{ url_for('static', path='css/highlight.css') }}" />
{% endif %}
```

`highlight.css` генерируется заранее CLI-утилитой `pygmentize` на основе темы `github-dark`.

---

## 4. Серверный рендеринг ANSI (для CLI-клиентов)

Если `User-Agent` совпадает с `curl`, `httpie` или `wget`, маршрут возвращает `text/plain` с ANSI-артом.

### 4.1. Определение CLI-клиента

```python
# app/views/deps.py
def is_cli_client(user_agent: Annotated[str | None, Header()]) -> bool:
    if not user_agent:
        return False
    return is_cli_client_by_user_agent(user_agent)

# app/views/utils.py
CLI_USER_AGENT_PATTERN = re.compile(r"\b(?:curl|httpie|wget)/[^\s]+\b", re.IGNORECASE)
```

### 4.2. Markdown → ANSI

```python
# app/services/ansi.py
def render_markdown_to_ansi(md_content: str, width: int = 79) -> str:
    console = Console(
        width=width, record=True, force_terminal=True, color_system="truecolor"
    )
    with console.capture() as cap:
        console.print(Markdown(md_content, code_theme="github-dark"))
    return cap.get()
```

Здесь используется библиотека `rich`: `rich.markdown.Markdown` парсит Markdown и рендерит его в ANSI-escape-последовательности.

### 4.3. ANSI-шаблоны

Шаблоны находятся прямо в `app/views/utils.py` и рендерятся через `jinja2.Template`:

```python
POST_ANSI_TEMPLATE = """
{{ post.header }}

\033[1;97m{{ post.title }}\033[0m

\033[90m{{ author.full_name }}\033[0m

\033[90m{{ post.reading_time }}\t{{ post.publish_date }}\033[0m

{{ post.body }}\n
"""
```

Ответ возвращается как `PlainTextResponse`:

```python
return PlainTextResponse(
    render_ansi_template(template),
    status_code=status_code,
)
```

---

## 5. Что делает клиент (браузер)

Клиент получает **уже готовый HTML** и статику:

```text
1. Client → Caddy :80/:443
2. Caddy /static/* → file_server /srv/static/
3. Caddy /*         → reverse_proxy www:4000
4. FastAPI → Jinja2Templates → HTMLResponse
```

В `app/templates/layout/base.html` подключаются:

```html
<link href="{{ url_for('static', path='css/styles.css') }}" rel="stylesheet" />
```

CSS генерируется из `app/assets/input.css` через Tailwind CSS на этапе сборки (`pnpm build:css`).

Единственный клиентский JavaScript в шаблоне поста — кнопка "Share", копирующая ссылку в буфер обмена:

```html
<script type="text/javascript">
  const copyLink = () => {
    navigator.clipboard.writeText(
      "{{ url_for('post_detail', slug=post.slug) }}"
    );
    // ... UI-анимация
  };
</script>
```

Это не относится к рендерингу Markdown.

---

## 6. Жизненный цикл контента

```text
content/posts/my-post/index.md
         │
         ▼
get_content_objects(POSTS_CONTENT_DIR)
         │
         ▼
get_content_context(path) → ContentContext
         │
         ▼
move_image(context) → app/static/images/posts/my-post/*
         │
         ▼
load_markdown_content() → MarkdownContent
         │
         ▼
_parse_markdown() / render_markdown_to_ansi()
         │
         ▼
PublishedContent / PostANSIContent
         │
         ▼
словарь posts[slug] → get_content() / get_ansi_content()
```

Кэширование:

- `get_content()` и `get_ansi_content()` декорированы `@cache` (`functools.cache`).
- Кэш заполняется один раз при старте в `lifespan`.
- Перечитать контент можно только перезапуском процесса.

---

## 7. Почему нет клиентского рендеринга

В проекте отсутствуют:

- JavaScript-библиотеки для Markdown (`marked`, `remark`, `rehype`, `mdx`).
- React/Vue/Svelte-компоненты для рендеринга контента.
- `package.json` содержит только Tailwind CSS:

```json
{
  "scripts": {
    "dev:css": "tailwindcss -i app/assets/input.css -o app/static/css/styles.css --watch=always",
    "build:css": "tailwindcss -i app/assets/input.css -o app/static/css/styles.css --minify"
  },
  "devDependencies": {
    "tailwindcss": "4.3.0",
    "@tailwindcss/cli": "4.3.0"
  }
}
```

Поиск по ключевым словам (`markdown`, `marked`, `remark`, `mdx`) в исходниках `.ts`, `.tsx`, `.js`, `.jsx` не даёт результатов.

---

## 8. Итоговая таблица

| Аспект | Где происходит | Инструменты |
|--------|----------------|-------------|
| Парсинг Markdown → HTML | Сервер | Python `markdown` (`fenced_code`, `codehilite`) |
| Постобработка HTML | Сервер | `BeautifulSoup4` |
| Подсветка кода | Сервер (генерация CSS) | `Pygments` (`github-dark`) |
| Стилизация | Сервер (классы в HTML) + сборка CSS | Tailwind CSS |
| Рендеринг шаблонов | Сервер | Jinja2 (`fastapi.templating.Jinja2Templates`) |
| Markdown → ANSI | Сервер | `rich.markdown.Markdown` |
| Отдача браузеру | Сервер | FastAPI `HTMLResponse` |
| Отдача CLI | Сервер | FastAPI `PlainTextResponse` |
| Клиентский JS | Браузер | Только кнопка "Share" |

---

## 9. Вывод

**Markdown рендерится исключительно на сервере.** Браузер и CLI-клиенты получают готовый HTML или ANSI-арт. Архитектура соответствует классическому серверному рендерингу (SSR): контент парсится один раз при старте, кэшируется в памяти и отдаётся по запросу.

**Проблема потребления памяти при росте контента** рассмотрена отдельно в [`06_memory_analysis_and_optimization.md`](./06_memory_analysis_and_optimization.md).

---

## 10. Ссылки

| Файл | Описание |
|------|----------|
| [`01_project_structure.md`](./01_project_structure.md) | Карта проекта, дерево директорий, зависимости |
| [`02_architecture.md`](./02_architecture.md) | Архитектура, паттерны проектирования, схема потока данных |
| [`03_execution_flow.md`](./03_execution_flow.md) | Жизненный цикл, роутинг, обработка ошибок |
| [`04_data_model_and_content.md`](./04_data_model_and_content.md) | Форматы контента, фронтматтер, модели |
| [`05_markdown_rendering_report.md`](./05_markdown_rendering_report.md) | Как рендерится Markdown (этот файл) |
| [`06_memory_analysis_and_optimization.md`](./06_memory_analysis_and_optimization.md) | Анализ памяти, варианты оптимизации |

---

## 10. Анализ потребления памяти и пути оптимизации

### 10.1. Текущее поведение

При запуске приложения (`lifespan`) вызываются две кэшированные функции:

```python
# app/views/routes.py
@asynccontextmanager
async def lifespan(_: FastAPI):
    get_content()          # ← HTML-контент
    get_ansi_content()     # ← ANSI-контент
    yield
```

Результат сохраняется в `functools.cache` и хранится в памяти до перезапуска процесса. При этом данные загружаются **все сразу**, даже если пользователь запрашивает только один пост.

### 10.2. Оценка потребления памяти

Каждый пост/проект после `model_dump()` превращается в Python-словарь. Примерный размер одного поста:

| Поле | Размер |
|------|--------|
| `title` | ~50 B |
| `description` | ~200 B |
| `slug` | ~30 B |
| `body` (HTML) | ~5 000–50 000 B |
| `publish_date`, `topic`, `repository` | ~100 B |
| `extras`, пути, служебные объекты | ~300 B |
| **Итого на пост** | **~6–100 KB** |

**Сценарии:**

| Размер контента | Ориентировочная память |
|-----------------|------------------------|
| 100 постов по 5 KB | ~1 MB |
| 1 000 постов по 10 KB | ~20 MB |
| 10 000 постов по 10 KB | ~200 MB |
| 100 000 постов по 10 KB | ~2 GB |

### 10.3. Проблема дублирования

Существует **две независимые копии** всех постов:

1. `get_content()` → `dict[slug, PublishedContent]` (HTML)
2. `get_ansi_content()` → `dict[slug, PostANSIContent]` (ANSI)

Каждая хранит полный `body` поста. Это **удваивает** потребление памяти для одного и того же контента.

### 10.4. Когда станет проблемой

| Ситуация | Вердикт |
|----------|---------|
| Блог, 10–100 постов | ✅ Нет проблем, память ~1–10 MB |
| Портфолио, 10–50 проектов | ✅ Нет проблем, память ~1–5 MB |
| Документация, 1 000+ страниц | ⚠️ Возможно, 20–100 MB |
| Wiki, 10 000+ страниц | ❌ Да, нужно менять подход |

---

## 11. Варианты оптимизации

### Вариант 1: Ленивая загрузка (по запросу)

Убрать `@cache` и читать файл только когда запросили конкретный slug:

```python
def get_post(slug: str) -> dict:
    for post_path in POSTS_CONTENT_DIR.glob("*/index.md"):
        content = _load_post(post_path)
        if content.slug == slug:
            return content.model_dump()
    raise HTTPException(404)
```

**Плюсы:** память не растёт с количеством файлов.
**Минусы:** медленнее при первом запросе каждого поста.

### Вариант 2: Индекс + ленивая загрузка (рекомендуемый)

Хранить в памяти только индексы (slug, title, date, description), а тело читать по запросу:

```python
@cache
def get_post_index() -> list[dict]:
    return [{"slug": p.slug, "title": p.title, "date": p.date}
            for p in _load_all_posts()]

def get_post_detail(slug: str) -> dict:
    post = _load_post_from_disk(slug)  # читаем только этот файл
    return post.model_dump()
```

**Плюсы:** минимальная память, быстрая отдача списков, данные всегда актуальны.
**Минусы:** немного сложнее код, нужен дополнительный запрос к ФС для детальной страницы.

### Вариант 3: SQLite-хранилище

При старте один раз прочитать все файлы и записать в локальную БД. При запросе — `SELECT * FROM posts WHERE slug = ?`:

```python
# При старте
for post_file in posts_dir.glob("*/index.md"):
    content = _parse_post(post_file)
    db.execute("INSERT INTO posts VALUES (?, ?, ?)",
               (content.slug, content.title, content.body))

# При запросе
post = db.execute("SELECT * FROM posts WHERE slug = ?", (slug,)).fetchone()
```

**Плюсы:** быстрый поиск, поддержка SQL-запросов, данные отделены от кода.
**Минусы:** нужна миграция, усложнение архитектуры.

---

## 12. Итог

| Ситуация | Рекомендация |
|----------|--------------|
| Текущий блог/портфолио | ✅ Текущий подход оптимален (простота важнее) |
| Рост до 1 000+ страниц | ⚠️ Внедрить Вариант 2 (индекс + ленивая загрузка) |
| > 10 000 страниц или сложные запросы | ❌ Переходить на Вариант 3 (SQLite) |
