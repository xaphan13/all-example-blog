# AGENTS.md — инструкции для ИИ-агентов

Этот файл содержит контекст и правила работы с репозиторием `luovkle.com`. Читай его перед любыми изменениями в кодовой базе.

## 📖 Первоочередной источник знаний: `docs/`

**Перед началом работы обязательно изучи документацию в [`docs/`](docs/) — она подробная и актуальная:**

| Документ | Когда читать |
|----------|--------------|
| [docs/01_project_structure.md](docs/01_project_structure.md) | Чтобы понять назначение любой директории/файла и роли зависимостей |
| [docs/02_architecture.md](docs/02_architecture.md) | Перед изменением архитектуры, сервисного слоя, кэширования |
| [docs/03_execution_flow.md](docs/03_execution_flow.md) | Перед изменением роутов, обработчиков ошибок, lifespan, шаблонов |
| [docs/04_data_model_and_content.md](docs/04_data_model_and_content.md) | Перед изменением Pydantic-схем или формата контента/frontmatter |
| [docs/05_deployment_and_operations.md](docs/05_deployment_and_operations.md) | Перед изменением Containerfile, compose-файлов, Makefile |
| [docs/05_markdown_rendering_report.md](docs/05_markdown_rendering_report.md) | Перед изменением пайплайна рендеринга Markdown |
| [docs/06_memory_analysis_and_optimization.md](docs/06_memory_analysis_and_optimization.md) | Перед оптимизацией потребления памяти |
| [docs/local-development.md](docs/local-development.md) | Перед изменением Makefile или workflow локальной разработки |

Документация на русском языке. Если документация и код расходятся — код является истиной, но сообщи об этом пользователю.

## 🧠 Что это за проект

Персональный блог и портфолио разработчика: **монолитный SSR-сайт на FastAPI без базы данных**.

Ключевые факты, которые определяют все решения:

1. **Контент = файлы.** Статьи и проекты — Markdown с YAML-фронтматтером в `content/posts/<slug>/index.md` и `content/projects/<slug>/index.md`. Никакой БД, никакой админки.
2. **Двойной рендеринг.** Один и тот же маршрут отдаёт HTML (браузерам, Jinja2 + Tailwind) или ANSI-арт (`text/plain` для `curl`/`httpie`/`wget`, определяется по `User-Agent` в `app/views/deps.py`). Любое изменение контентного пайплайна должно работать в **обоих** представлениях (`app/services/html.py` и `app/services/ansi.py`).
3. **In-memory кэш без инвалидации.** `get_content()` и `get_ansi_content()` декорированы `functools.cache` и eagerly загружаются в `lifespan` при старте. Изменения в `content/` требуют **перезапуска процесса**. Инвалидации в рантайме нет.
4. **OpenAPI отключён** (`FastAPI(openapi_url=None)`) — это сайт, а не API. Не добавляй эндпоинты, рассчитанные на API-клиентов, без обсуждения.
5. **Переменных окружения в приложении нет.** Конфигурация — через `Path`-константы в `app/config.py` и compose/Makefile.
6. **Генерируемые артефакты не хранятся в репозитории:** `app/static/css/styles.css`, `highlight.css`, `app/static/images/{author,posts,projects}/`, `*.webp`/`*.avif`, `app/ansi/`. Их создают Makefile/CLI/Containerfile. Не редактируй и не коммить их.

## 🏗️ Структура (кратко)

```text
app/
├── main.py           # Точка входа FastAPI
├── config.py         # Path-константы
├── schemas.py        # Pydantic-модели (MetadataMD, PostMD, ProjectMD, PublishedContent, ...)
├── types.py          # TypedDict для внутренних словарей
├── services/         # Content-provider слой
│   ├── common.py     # Чтение Markdown/YAML, слаги, копирование изображений
│   ├── html.py       # HTML-контекст (@cache get_content)
│   └── ansi.py       # ANSI-контекст (@cache get_ansi_content)
├── views/
│   ├── routes.py     # Маршруты, lifespan, обработчики ошибок
│   ├── deps.py       # is_cli_client (по User-Agent)
│   └── utils.py      # ANSI-шаблоны, CLI_USER_AGENT_PATTERN
├── templates/        # Jinja2 (layout/, includes/, страницы, 404/500)
└── static/           # Генерируемые ассеты
cli/                  # convert_images.py, img_to_ansi.py
content/              # Markdown-контент (meta.md, homepage.md, author/, posts/, projects/)
caddy/                # Caddyfile + Containerfile'ы
scripts/              # format.sh, lint.sh
```

## ⌨️ Команды

Все операции — через `make` (см. [docs/local-development.md](docs/local-development.md)):

```bash
make setup           # uv sync --all-groups + pnpm install + prek install
make local-dev       # fastapi dev на :4000 (порт: make local-dev PORT=8000)
make local-prod      # fastapi run на :4000
make dev / stage / prod   # podman-compose up -d --build
make {env}-stop      # остановка окружения
make format          # ruff + djlint --reformat
make lint            # ty + ruff + djlint
make check           # prek run --all-files
make images-optimize # PNG/JPEG → WebP/AVIF (stamp в .cache/)
make images-ansi     # PNG-обложки → ANSI-арт (stamp в .cache/)
make clean / fclean / re
```

Контейнерный инструмент: `podman-compose` (переопределяется `CONTAINER_TOOL=...`). Docker-совместимость в процессе.

## 📐 Конвенции кода

- **Python 3.13+**, менеджер зависимостей — `uv` (не pip). Группы зависимостей: `main`, `build` (Pillow), `dev`.
- **Линтеры:** `ruff` (включены правила `E`, `W`, `F`, `I`, `B`, `C4`, `UP`, `ARG001`, `T201` — **print-выражения запрещены**), `ty` (type checker), `djlint` (Jinja2-шаблоны, профиль `jinja`, отступ 2).
- Перед коммитом: `make format && make lint` (или `make check`).
- Комментарии и документация проекта — на русском языке; код и идентификаторы — на английском.
- Pydantic-модели — в `app/schemas.py`; TypedDict — в `app/types.py`. Не смешивай.
- Пути к файлам/директориям — только через константы `app/config.py` (и `cli/config.py` для CLI). Не хардкодь пути.
- Post-commit хуки (`prek`): не отключай проверки в `.pre-commit-config.yaml`.

## ⚠️ Подводные камни

- **Кэш:** после правок в `content/` или сервисном слое перезапусти процесс, иначе увидишь старый контент.
- **Frontmatter валидируется Pydantic при старте** — невалидный YAML в `content/` уронит lifespan с `ValidationError`. Обязательные поля см. в [docs/04_data_model_and_content.md](docs/04_data_model_and_content.md).
- **Markdown-постобработка:** `BeautifulSoup` в `_parse_markdown` перезаписывает `src` локальных изображений в Jinja2-выражения `url_for('static', ...)` и вешает Tailwind-классы. Внешние ссылки/пустые `src` игнорируются; из `src` берётся только имя файла (защита от path traversal) — не нарушай это.
- **Обложки** выбираются детерминированно по длине заголовка (`get_cover_number`) из пула `cover_NNN.png` — не «чинить» это на произвольные картинки.
- **HTML-шаблоны содержат Jinja2-выражения внутри контента** (`url_for(...)` в `src`) — они разрешаются при рендере шаблона, не в сервисном слое.
- **Stamp-файлы** (`.venv/.deps-installed`, `node_modules/.deps-installed`, `.cache/*.stamp`) — механизм инкрементальности Makefile. При изменении входных данных make сам пересчитает; вручную stamp-файлы не трогай.
- **Безопасность контейнеров:** `read_only`, `cap_drop: [ALL]`, `no-new-privileges`, nonroot (uid/gid 999), Caddy удаляет `Server`/`Via`. Не ослабляй без явного запроса пользователя.
- **Порты:** `dev` — 80 и 4000; `stage`/`prod` — 80 и 443. Убедись, что они свободны перед запуском.

## ✅ Чек-лист перед завершением задачи

1. Изучил ли соответствующий документ из `docs/`?
2. `make lint` проходит?
3. Если менял контентный пайплайн — проверил и HTML, и ANSI-ветки (`curl http://localhost:4000/p` при запущенном `make local-dev`)?
4. Если менял Makefile/Containerfile/compose — сверился с [docs/05_deployment_and_operations.md](docs/05_deployment_and_operations.md)?
5. Не закоммитил ли генерируемые артефакты?
