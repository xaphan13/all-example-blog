# Деплой и операции

## Среды развёртывания

Проект поддерживает три среды через `podman-compose`:

| Среда | Команда запуска | Команда остановки | Особенности |
|-------|-----------------|-------------------|-------------|
| `dev` | `make dev` | `make dev-stop` | Hot-reload CSS и приложения, Caddy на порту 80, www на 4000 |
| `stage` | `make stage` | `make stage-stop` | Производственная сборка, hardened-контейнеры, Caddy reverse proxy |
| `prod` | `make prod` | `make prod-stop` | Использует предварительно собранные образы `localhost/luovklecom_*` |

## Сервисы в compose

### `compose.dev.yaml`

- `www` — target `runner`, команда `fastapi dev`, volume-монтирование `app/` и `content/`.
- `styles` — target `css-builder`, команда `pnpm run dev:css`, пересобирает CSS при изменениях.
- `caddy` — локальный Caddy на `:80`, раздаёт `app/static/`.

### `compose.stage.yaml`

- `www` — read-only rootfs, `cap_drop: ALL`, `no-new-privileges`, изолированная сеть, healthcheck.
- `caddy` — `NET_BIND_SERVICE` для `:80`/`:443`, public + isolated сети.
- Общий volume `static_files` для статики.

### `compose.prod.yaml`

- Аналогичен `stage`, но `www` и `caddy` используют заранее собранные образы.
- Дополнительные volumes `caddy_data` и `caddy_config` для TLS и конфигурации.

## Многостадийная сборка (`Containerfile`)

```text
1. css-builder         node:22-trixie-slim
   └── pnpm install → build:css

2. convert-images-builder  ghcr.io/astral-sh/uv:python3.13-trixie-slim
   └── uv sync --only-group build (Pillow)

3. convert-images          python:3.13-slim-trixie
   └── копирует .venv + cli/ + images/
   └── RUN python -m cli.convert_images
   └── RUN python -m cli.img_to_ansi

4. runner-builder          ghcr.io/astral-sh/uv:python3.13-trixie-slim
   └── uv sync --no-dev (production deps)

5. runner                  python:3.13-slim-trixie
   └── копирует .venv, app/, content/, ANSI-арт, обработанные изображения, CSS
   └── генерация highlight.css
   └── USER nonroot
   └── CMD fastapi run --port 4000 --host 0.0.0.0 ...
```

## Локальная разработка без контейнеров

```bash
make setup          # uv sync + pnpm install + pre-commit
make local-dev      # сборка всех артефактов + fastapi dev
make local-prod     # сборка всех артефактов + fastapi run
make local-styles   # только pnpm run dev:css
```

### Артефакты, генерируемые локально

```bash
app/static/css/styles.css      # Tailwind
app/static/css/highlight.css   # Pygments
cache/images-optimize.stamp    # WebP/AVIF
cache/images-ansi.stamp        # ANSI-арт
```

## Обработка изображений

```bash
make images-optimize  # PNG/JPEG → WebP/AVIF, только если меньше оригинала
make images-ansi      # PNG обложки → ANSI-арт
```

Обе команды используют stamp-файлы в `.cache/`, чтобы избежать повторной работы.

## Линтинг и форматирование

```bash
make format  # ruff check --fix + ruff format + djlint --reformat
make lint    # ty check + ruff check + ruff format --check + djlint check/lint
make check   # prek run --all-files (pre-commit hooks)
```

Используемые инструменты:

- `ruff` — Python linter/formatter.
- `ty` — type checker (альтернатива mypy/pyright).
- `djlint` — linter/formatter Jinja2-шаблонов.
- `prek` / `.pre-commit-config.yaml` — pre-commit хуки.

## Healthcheck

- `www`: `HEAD /health` → `204 No Content` (`app/views/routes.py::health`).
- `caddy`: `GET /` → `200 OK`.
- Проверки запускаются каждые 30s, timeout 5s, 3 попытки, `start_period` 15s.

## Операционные процедуры

### Добавление нового поста

1. `mkdir content/posts/<slug>`
2. Создать `index.md` с frontmatter.
3. Добавить `images/` при необходимости.
4. `make stage-stop && make stage` (или рестарт dev-контейнера).

### Обновление зависимостей

- Python: `uv add <pkg>` или редактирование `pyproject.toml` + `uv lock`.
- Node: `pnpm add -D <pkg>` или редактирование `package.json` + `pnpm install`.

### Очистка артефактов

```bash
make clean   # удаляет generated CSS, webp/avif, ANSI, __pycache__, .cache
make fclean  # clean + удаляет .venv, node_modules, .ruff_cache
make re      # fclean + make stage
```

## Порты

| Среда | Публичные порты | Сервис | Внутренний порт |
|-------|-----------------|--------|-----------------|
| dev | `80`, `4000` | caddy | 80 |
| dev | `4000` | www | 4000 |
| stage/prod | `80`, `443`, `443/udp` | caddy | 80/443 |
| stage/prod | — | www | 4000 (expose) |

## Безопасность контейнеров

- `read_only: true` для `www`.
- `cap_drop: ALL` + `no-new-privileges:true`.
- Пользователь `nonroot` (uid/gid 999) в `runner`.
- Caddy удаляет `Server` и `Via` заголовки.
- `forwarded-allow-ips *` в FastAPI позволяет доверять `X-Forwarded-*` от Caddy.
