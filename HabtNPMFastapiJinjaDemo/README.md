# FastAPI + Jinja2 + Tailwind — demo project

A minimal but well-architected web application built with FastAPI, server-side
rendering via Jinja2, and Tailwind CSS styling. This project serves as **a
demonstration for an article**: the goal is not feature richness, but a clear
and scalable architecture you can rely on in a real application.

---

## Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.137.0 | Async web framework, routing, validation |
| [Uvicorn](https://www.uvicorn.org/) | 0.49.0 | ASGI server (`[standard]` provides uvloop, httptools, watchfiles) |
| [Jinja2](https://jinja.palletsprojects.com/) | 3.1.6 | Server-side HTML rendering |
| [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | 2.14.1 | Configuration from environment variables / `.env` |
| [python-multipart](https://github.com/Kludex/python-multipart) | 0.0.32 | Form-data parsing for HTML forms |
| [Tailwind CSS](https://tailwindcss.com/) | CDN | Utility-first styling without a build step |

---

## Quick start

```bash
# virtual environment is already set up in ./venv
source venv/bin/activate
pip install -r requirements.txt

python3 main.py          # → http://127.0.0.1:8000
```

API documentation (Swagger) is available at `http://127.0.0.1:8000/docs`.

---

## Project structure

```
NPMPythonDemoProject/
├── main.py              # entry point: application factory + uvicorn launch
├── router.py            # aggregator: collects all sub-routers into one object
├── requirements.txt
├── core/                # application infrastructure
│   ├── config.py        # settings (pydantic-settings)
│   └── templating.py    # single Jinja2Templates instance
├── routers/             # routes grouped by concern
│   ├── pages.py         # HTML pages (/, /about)
│   └── api.py           # JSON API (/api/...)
├── static/              # served as-is under /static/...
│   ├── css/style.css    # custom CSS on top of Tailwind
│   └── js/main.js       # client-side logic
└── templates/           # Jinja2 templates
    ├── base.html        # base layout (Tailwind is loaded here)
    ├── partials/        # reusable components (navbar, footer)
    └── pages/           # per-page content
```

---

## Architectural decisions and rationale

### 1. Application factory `create_app()`

In [main.py](main.py), the application is assembled inside the `create_app()`
function rather than being created as a global object at the module level.

**Why:** The factory isolates application assembly. This simplifies testing
(you can create a separate instance with different settings), eliminates
side-effects on import, and draws a clear boundary: "this is where the
application is fully assembled." Running via `uvicorn.run("main:app", ...)`
under `if __name__ == "__main__"` lets you start with a single
`python3 main.py` command while keeping `--reload` working.

### 2. `router.py` — single point for registering routers

`main.py` knows nothing about specific pages: it imports a single `router`
object from [router.py](router.py), which in turn includes sub-routers from
the `routers/` package.

**Why:** Adding a new section takes two steps — create a module in `routers/`
and add one `include_router` line. `main.py` stays unchanged. This prevents
the "bedsheet" problem: routes don't accumulate in one file but grow
horizontally by domain.

### 3. Separation of `pages` and `api`

Pages ([routers/pages.py](routers/pages.py)) and JSON endpoints
([routers/api.py](routers/api.py)) live in separate routers. The API is
placed under the `/api` prefix and tagged accordingly.

**Why:** HTML and REST have different response formats, different consumers,
and different evolution paths. Separation makes the boundary between
"serving pages" and "serving data" explicit, and tags neatly group endpoints
in `/docs`.

### 4. `core/` layer — infrastructure separated from routes

`core/` holds everything that isn't tied to specific endpoints:
configuration and template engine setup.

- [core/config.py](core/config.py) — a `Settings` class built on
  pydantic-settings. All parameters (host, port, paths, debug) are read from
  the environment / `.env` with type validation. A single `settings` instance
  is the single source of truth — no magic constants scattered across the
  codebase.
- [core/templating.py](core/templating.py) — a single `Jinja2Templates`
  instance. Global template variables (e.g. `app_name`) and future filters
  are set in one place; routers simply import the ready-made `templates`.

**Why:** Infrastructure code tends to leak into handlers. Moving it to
`core/` keeps routers thin and focused on route-specific logic.

### 5. Templates via inheritance and partials

[templates/base.html](templates/base.html) defines the common layout; pages
in `templates/pages/` extend it with `{% extends %}` and only fill the
`content` block. Repeated parts (navbar, footer) are extracted into
`partials/` and included via `{% include %}`.

**Why:** No template duplicates `<head>`, style includes, or page structure.
Change the layout — fix one file. This is a direct application of the DRY
principle at the markup level.

### 6. Tailwind via CDN instead of npm build

Tailwind is loaded via a `<script src="https://cdn.tailwindcss.com">` tag
directly in `base.html`.

**Why:** This is a demo project, and the goal is to showcase the backend
architecture, not frontend build tooling. CDN removes `package.json`,
`node_modules`, and a CSS compilation step — you can run it immediately. In
production, Tailwind is set up via CLI/PostCSS with unused-class purging,
but for an article that overhead would only be a distraction. The
`static/css/` folder remains available for custom styles on top of Tailwind.

### 7. Modern `TemplateResponse` signature

Templates are rendered as `templates.TemplateResponse(request, "name.html", {...})`
— with `request` as the first argument.

**Why:** This is the current Starlette/FastAPI API. The old form
(`TemplateResponse("name.html", {"request": request, ...})`) is deprecated,
so we use the new one to avoid deprecation warnings and stay valid on recent
versions.

---

## How to extend

- **New page:** add a handler in `routers/pages.py` and a template in
  `templates/pages/`.
- **New API section:** create a module in `routers/` and wire it with one
  line in `router.py`.
- **Business logic:** as the codebase grows, extract logic from handlers
  into a dedicated `services/` layer, keeping routers thin.
- **New config parameter:** add a field to `Settings` — it is immediately
  read from the environment / `.env`.
