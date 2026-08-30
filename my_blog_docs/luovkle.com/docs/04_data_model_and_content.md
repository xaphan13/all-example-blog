# Модели данных и формат контента

## Обзор моделей данных

Все модели определены в `app/schemas.py` на базе `pydantic.BaseModel`. Они описывают:

- метаданные сайта (`MetadataMD`);
- данные автора (`AuthorMD`);
- описания главной страницы (`HomepageMD`);
- контент статей и проектов (`PostMD`, `ProjectMD`, `MarkdownContent`);
- публикационные сущности (`PublishedContent`, `GenericANSIContent`);
- URL обложек (`CoverUrls`).

## Иерархия моделей

```text
Extras
    └── code: bool = False

ContentMD
    ├── extras: Extras
    ├── content: str | None = None
    ├── PostMD
    │       ├── title: str
    │       ├── description: str | None
    │       ├── slug: str | None
    │       ├── date: str | None
    │       └── topic: str | None
    └── ProjectMD
            ├── title: str
            ├── description: str | None
            ├── repository: str | None
            ├── website: HttpUrl | None
            ├── slug: str | None
            └── date: str | None

MetadataMD
    ├── description, keywords, author, language, robots
    ├── og:title, og:description, og:image, og:url, og:type, og:locale
    └── twitter:card, twitter:title, twitter:description, twitter:image, twitter:creator

HomepageMD
    ├── posts_section_description: str
    └── projects_section_description: str

AuthorMD
    ├── picture: str
    ├── full_name: str
    ├── role: str
    ├── about: str
    ├── github_url: HttpUrl | None
    └── linkedin_url: HttpUrl | None

MarkdownContent
    ├── title: str
    ├── description: str | None
    ├── repository: HttpUrl | None
    ├── website: HttpUrl | None
    ├── slug: str | None
    ├── date: str | None
    ├── topic: str | None
    └── body: str | None

PublishedContent
    ├── slug, title, body, description
    ├── repository, website, topic
    ├── thumbnail_path, cover_image_path
    ├── reading_time_minutes, publish_date
    ├── extras
    └── computed: reading_time, cover_image, thumbnail

CoverUrls
    ├── default: Path
    ├── avif: Path | None
    ├── webp: Path | None
    └── computed: default_url, avif_url, webp_url

GenericANSIContent
    ├── slug, header, thumbnail, title, publish_date
    ├── body, reading_time_minutes, description
    ├── repository, website, topic
    └── computed: reading_time

PostANSIContent(GenericANSIContent)
ProjectANSIContent(GenericANSIContent)
    └── ansi_description: list[str] | None
```

## Формат Markdown-контента

Каждый файл контента должен содержать YAML frontmatter, окружённый `---`:

```markdown
---
key: value
---

Markdown body here.
```

### Обязательные и опциональные поля

| Файл | Обязательные поля | Опциональные поля |
|------|-------------------|-------------------|
| `content/meta.md` | `description`, `keywords`, `author`, `language`, `robots`, `og:title`, `og:description`, `og:url`, `og:type`, `og:locale`, `twitter:card`, `twitter:title`, `twitter:description`, `twitter:creator` | `og:image`, `twitter:image` |
| `content/homepage.md` | `posts_section_description`, `projects_section_description` | — |
| `content/author/index.md` | `picture`, `full_name`, `role`, `about` | `github_url`, `linkedin_url` |
| `content/posts/<slug>/index.md` | `title` | `description`, `slug`, `date`, `topic`, `content` body |
| `content/projects/<slug>/index.md` | `title` | `description`, `repository`, `website`, `slug`, `date`, `content` body |

### Структура директории контента

```text
content/
├── posts/
│   └── example-post/
│       ├── index.md
│       └── images/
│           └── diagram.png
└── projects/
    └── example-project/
        ├── index.md
        └── images/
            └── screenshot.png
```

- Для постов/проектов допускается как поддиректория с `index.md`, так и standalone `.md`-файл.
- Изображения контента кладутся в `<dir>/images/`; они копируются в `app/static/images/<content_type>/<dir_name>/` при старте.

## Производные поля

| Поле | Источник |
|------|----------|
| `slug` | `markdown_content.slug` или `get_slug(index_file)` |
| `publish_date` | `markdown_content.date` или `get_creation_date(index_file)` |
| `reading_time_minutes` | `estimate_reading_time(body)` — слова / 200 |
| `cover_image_path` | `_get_cover_urls(HEADERS_DIR, title).default` |
| `thumbnail_path` | `_get_cover_urls(THUMBNAILS_DIR, title).default` |
| `body` (HTML) | `_parse_markdown(content_context, body)` |
| `body` (ANSI) | `render_markdown_to_ansi(body)` |

## Типы-справочники

`app/types.py` определяет `TypedDict` для словарей, которые не проходят через Pydantic:

- `HeadersAndThumbnailsDict` — пары `headers`/`thumbnails` из `CoverUrls`.
- `ANSIContent` — словарь `posts`/`projects` с ANSI-моделями.
- `TemplateArgsDict` — флаги для Jinja2 (`code`).
- `ParsedMarkdownDict` — результат `_parse_markdown`: HTML-строка + `extras`.

## Рекомендации по добавлению контента

1. Создать директорию `content/posts/<my-slug>/` или `content/projects/<my-slug>/`.
2. Добавить `index.md` с валидным YAML frontmatter и Markdown-телом.
3. При необходимости добавить `images/` с локальными ресурсами.
4. Перезапустить приложение, чтобы инвалидировать in-memory кэш.
5. Убедиться, что `og_image`/`twitter_image` заполнены или fallback берётся из thumbnails.
