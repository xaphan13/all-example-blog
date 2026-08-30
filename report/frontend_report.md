# Отчёт по фронтенду: технологии и библиотеки во всех 6 проектах

> Дата: 2026-08-30. Источники: `my_blog_docs/<проект>/` (README, AGENTS, docs/01–07).
> Основа: готовые frontend-отчёты проектов (`AmiaBlog/docs/06_frontend_report.md`,
> `diegolonio-dot-com/docs/frontend_report.md`, `HabtNPMFastapiJinjaDemo/docs/06_frontend.md`,
> `fastapi-htmx-starter/docs/07_frontend.md`, `fastAPIuser-suren/docs/06_frontend_bootstrap_analysis.md`,
> `luovkle.com/docs/05_markdown_rendering_report.md`).

---

## 0. Сводная таблица

| # | Проект | Шаблонизация | CSS | Клиентский JS | Markdown | Подсветка кода | Сборка фронтенда |
|---|--------|--------------|-----|---------------|----------|----------------|------------------|
| 1 | **AmiaBlog** | Jinja2 (+ htmlmin) | MDUI v2 (Material Design, self-hosted) | Веб-компоненты MDUI + inline-скрипты + WebSocket (live-preview) | **На клиенте** (markdown-it 14.1.0 + плагин сносок) | highlight.js 11 (клиент, языки по требованию) | Нет |
| 2 | **diegolonio-dot-com** | Jinja2 | Ручной CSS (без фреймворков) | Один файл `editor.js` (админ-редактор), vanilla JS | **На сервере** (markdown-it-py + dollarmath), HTML кэшируется в PostgreSQL | Pygments (сервер) | Нет |
| 3 | **fastapi-htmx-starter** | Jinja2 (`.jinja2`) | Tailwind **Play CDN** | **HTMX 2.0.4** (partial swap) + ~150 строк inline vanilla JS | — (нет контента) | — | Нет |
| 4 | **fastAPIuser-suren** | Jinja2 | Bootstrap 5.3.7 (CDN, только CSS, SRI) | Inline JS с `fetch()` (верификация email) | — | — | Нет |
| 5 | **HabtNPMFastapiJinjaDemo** | Jinja2 (совр. `TemplateResponse(request, ...)`) | Tailwind **CDN** + 7 строк своего CSS | Один файл `main.js` (17 строк, fetch `/api/ping`) | — | — | Нет |
| 6 | **luovkle.com** | Jinja2 (HTML **и** ANSI-шаблоны) | Tailwind **4.3.0, локальная сборка** (pnpm + CLI) | Практически нет (только кнопка Share) | **На сервере** (Python `markdown` + BeautifulSoup) | Pygments (сервер, CSS `github-dark`) | **Да** — только Tailwind CSS (pnpm) |

**Общее для всех 6:** ни в одном проекте нет SPA-фреймворков (React/Vue/Angular/Svelte) и бандлеров JS (webpack/Vite/esbuild). Везде — серверный рендеринг на FastAPI + Jinja2, а вся клиентская логика — точечный vanilla JS.

---

## 1. AmiaBlog — фронтенд на веб-компонентах MDUI v2, Markdown рендерит браузер

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 + `htmlmin` (минификация HTML на сервере) | — | `templates/*.html` |
| UI-компоненты | **MDUI v2** (Material Design You, веб-компоненты `mdui-*`) | 2.1.4 | `static/mdui_2.1.4/` (self-hosted) |
| Шрифты/иконки | Roboto (`@font-face`), Material Icons | — | `static/roboto/`, `static/material_icons/` |
| Markdown | **markdown-it** + markdown-it-footnote | 14.1.0 / 4.0.0 | `static/` (self-hosted, **клиент**) |
| Подсветка кода | **highlight.js** | 11.1.1 | `static/hljs_11.1.1/` (клиент) |
| Live-preview | WebSocket (`/api/live-preview-ws`) | — | `static/live_preview.js` |

### Ключевые особенности

- **Markdown рендерится в браузере** — уникальный случай среди всех 6 проектов. Сервер отдаёт сырой Markdown в скрытом `<pre id="post-content">`, inline-скрипт разворачивает HTML-сущности и вызывает `markdown-it` (`html: true, linkify, typographer, breaks`) с плагином сносок.
- **Компонентная библиотека вместо CSS-фреймворка**: вся верстка — кастомные элементы (`mdui-navigation-drawer`, `mdui-card`, `mdui-chip`, `mdui-dialog` и др.), тема и акцентный цвет задаются из `config.json` (`mdui.setColorScheme(...)`).
- **Умная загрузка highlight.js**: сервер (`core/hljs.py`) сканирует пост на языки блоков кода и подключает только нужные языковые бандлы.
- **Live-preview через WebSocket**: клиент подписывается на slug, получает `update` (новый Markdown → перерендер) и `refresh` (перезагрузка страницы); heartbeat ping/pong каждые 5 с.
- **Двойной режим**: `is_static` в шаблонах добавляет суффиксы `.html` и скрывает поиск/live-preview — те же шаблоны работают и для динамики, и для `staticify.py` (генерация статики).
- Формы — обычные HTML GET/POST без AJAX (поиск, сортировка через перезагрузку страницы).

### Ограничения

- `markdown-it` с `html: true` без санитизации — доверие к автору контента.
- Нет Service Worker, lazy-loading, бандлеров; Markdown перерендеривается на каждой загрузке страницы.

---

## 2. diegolonio-dot-com — минималистичный SSR с ручным CSS и серверным Markdown

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 (`app/templating.py`, глобальные `base_url`, `static_v`, фильтр `dateformat`) | — | `app/templates/` |
| CSS | **Ручной CSS без фреймворков и препроцессоров** | — | `app/static/css/*.css` (base, home, post, about, search, pygments, admin/*) |
| JS | Vanilla JS, один файл **`editor.js`** | — | `app/static/js/editor.js` |
| Markdown | **markdown-it-py** (commonmark + table + strikethrough) + `dollarmath_plugin` | — | `app/markdown_render.py` (**сервер**) |
| Подсветка кода | **Pygments** (нумерация строк, `linenos="inline"`) | — | сервер |
| Формулы | **KaTeX 0.16.9** (CDN jsDelivr, `auto-render`) | 0.16.9 | `post.html`, `admin/form.html` |
| Иконки/бейджи | Font Awesome 6.5.1, devicon, shields.io (CDN) | — | `base.html`, `about.html` |

### Ключевые особенности

- **Markdown → HTML один раз, при сохранении поста**: готовый HTML кэшируется в PostgreSQL (`posts.content_html`), публичные страницы выводят `{{ post.content_html | safe }}`. Нулевая стоимость рендеринга на запрос.
- **Единственный клиентский JS — админ-редактор**: переключение Edit/Preview (preview через `POST /admin/api/preview` — тот же серверный рендер, что и публикация), drag&drop/paste загрузки изображений, теги-chips, auto-resize.
- **Формулы — гибрид**: сервер (`dollarmath_plugin`) конвертирует `$...$`/`$$...$$` в LaTeX-разметку `\(...\)`/`\[...\]`, финальный рендеринг делает KaTeX в браузере.
- **Cache busting через `?v={{ static_v }}`** (timestamp запуска сервера) на всех своих CSS/JS.
- Тёмной темы нет — один фиксированный стиль; CSS написан вручную, без `@apply`/препроцессоров.

### Ограничения

- KaTeX и иконки зависят от CDN; нет интерактивности на публичных страницах; нет пагинации в поиске/тегах.

---

## 3. fastapi-htmx-starter — идиоматичный HTMX + Tailwind (boilerplate)

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 (`app/core/templates.py`), 10 файлов `.jinja2` | — | `app/templates/` |
| CSS | **TailwindCSS Play CDN** | latest | `base.jinja2` |
| Интерактив | **HTMX** (partial swap) | ядро 2.0.4, ext `json-enc` ⚠️ 1.9.12 | unpkg CDN |
| JS | ~150 строк inline vanilla JS в 5 шаблонах | — | inline `<script>` |
| Свой CSS | `custom.css` (58 строк) | — | ⚠️ **файл нигде не подключён — мёртвый код** |

### Ключевые особенности

- **Единственный проект с HTMX**: сервер возвращает HTML-фрагменты, HTMX вставляет их в DOM. Полная карта взаимодействий: CRUD items (`hx-post`/`hx-get`/`hx-delete`/`hx-put`), inline-редактирование строки таблицы (замена `<tr id="item-{id}">` на форму и обратно), auth-формы, `hx-patch` профиля.
- **Продвинутые приёмы HTMX**: `hx-push-url="true"` (синхронизация URL, кнопки назад/вперёд), живой поиск с дебаунсом `hx-trigger="input changed delay:300ms, submit"`, `hx-confirm`, `hx-on::after-request`, индикатор загрузки.
- **Два режима кодирования тел**: `json-enc` (Pydantic-модели) для register/items/profile, form-data для login (требование fastapi-users `OAuth2PasswordRequestForm`).
- **Двухуровневая обработка ошибок**: глобальные `htmx:responseError`/`htmx:sendError` в `base.jinja2` + локальные в auth-формах с `stopPropagation()`.
- Вся верстка — утилитарные классы Tailwind; консистентная дизайн-система (карточки/кнопки/инпуты).

### Найденные проблемы (из отчёта проекта)

- 🔴 `custom.css` не подключён ни в одном шаблоне; 🔴 XSS в `profile.jinja2:42` (`user.email` в `onclick` без экранирования); 🟡 версии HTMX разъехались (2.0.4 vs 1.9.12); 🟡 Play CDN Tailwind не для production; 🟡 inline JS несовместим с CSP.

---

## 4. fastAPIuser-suren — Jinja2 + Bootstrap 5.3 через CDN

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 (`jinja_templates.py`), 6 шаблонов | — | `fastapi-application/templates/` |
| CSS | **Bootstrap 5.3.7 через CDN (jsDelivr), только CSS, с SRI-integrity** | 5.3.7 | `base.html` |
| JS | Inline vanilla JS с `fetch()` | — | inline в `home.html`, `verification.html` |
| Email-шаблоны | Отдельные Jinja2-шаблоны без Bootstrap | — | `templates/mailing/` |
| Админка | SQLAdmin (готовый UI, вне Jinja-фронтенда) | — | `admin/` |

### Ключевые особенности

- **Bootstrap подключён без JS-бандла** (`bootstrap.bundle.min.js` не загружается) — интерактивные компоненты Bootstrap (modals, dropdowns) не используются; весь интерактив — собственный JS с `fetch()` на `/api/v1/auth/*` (запрос токена верификации, подтверждение email по token из query).
- Используются утилитарные классы Bootstrap: сетка `container`, `list-group`, `badge text-bg-*`, `btn`, `spinner-border`, `alert`, `d-none`, `d-flex`.
- **Хорошая практика: SRI-хэш** на CDN-ссылке — единственный проект с integrity-атрибутом.
- Есть **email-шаблоны** (письма верификации) — тоже часть фронтенда, но без CSS (проблема для почтовых клиентов).
- HTML-страниц мало (home, verification): нет HTML-форм login/register/logout/reset-password — API есть, веб-форм нет.

### Ограничения

- Нет каталога `static/` вообще (`StaticFiles` не смонтирован) — весь JS inline; нет favicon, OG-тегов, тёмной темы (`data-bs-theme` не настроен), кастомизации Bootstrap.

---

## 5. HabtNPMFastapiJinjaDemo — учебное демо: Jinja2 + Tailwind CDN

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 3.1.6, современный API `TemplateResponse(request, ...)` | 3.1.6 | `templates/` (base + partials + pages) |
| CSS | **Tailwind через CDN** (`cdn.tailwindcss.com`) + 7 строк своего CSS | — | `base.html`, `static/css/style.css` |
| JS | Один файл **`main.js`, 17 строк** (fetch `/api/ping`) | — | `static/js/main.js` |

### Ключевые особенности

- **Самый маленький фронтенд — ~115 строк суммарно**; проект демонстрирует backend-архитектуру (`create_app()`, слои), фронтенд — сознательный минимум.
- Образцовая структура шаблонов: `base.html` (sticky-footer layout на flex) ← `pages/*` через `{% extends %}`, партиалы `navbar`/`footer` через `{% include %}`, глобальная переменная `app_name` в `templates.env.globals`.
- Единственная динамика — кнопка Ping: `fetch("/api/ping")` → вывод JSON-ответа; тот же origin, CORS не нужен.
- Tailwind-классы: палитра `slate` + акцент `indigo`, единственный брейкпоинт `sm:`, адаптивная сетка карточек.
- Компромиссы Tailwind CDN (≈3 МБ, компиляция в браузере, несовместимость со строгим CSP) разобраны в `docs/05_tailwind_cdn_vs_production.md` с планом миграции на production-сборку.

---

## 6. luovkle.com — двойной рендеринг HTML/ANSI, единственный проект со сборкой CSS

### Технологии и библиотеки

| Слой | Технология | Версия | Где живёт |
|---|---|---|---|
| Шаблоны | Jinja2 — **два набора**: HTML-шаблоны и ANSI-шаблоны | — | `app/templates/`, `app/views/utils.py` |
| CSS | **Tailwind CSS 4.3.0 — локальная сборка через pnpm + `@tailwindcss/cli`** (`input.css` → `styles.css`, `--minify`) | 4.3.0 | `package.json`, `app/assets/input.css` |
| Подсветка кода | **Pygments** (сервер, тема `github-dark`, CSS генерируется `pygmentize`) | — | сервер, `highlight.css` |
| Markdown → HTML | Python **`markdown`** (`fenced_code`, `codehilite`) + **BeautifulSoup4** (постобработка) | — | `app/services/html.py` (**сервер**) |
| Markdown → ANSI | **rich** (`rich.markdown.Markdown`, truecolor) | — | `app/services/ansi.py` (**сервер**) |
| Клиентский JS | Только кнопка Share (`navigator.clipboard.writeText`) | — | inline в шаблоне поста |

### Ключевые особенности

- **Уникальная фича — двойной рендеринг по User-Agent**: браузер получает HTML (`markdown` + BeautifulSoup + Jinja2), CLI-клиенты (`curl`, `httpie`, `wget` — определяется регуляркой по User-Agent) получают ANSI-арт через `rich` + PlainTextResponse. Один и тот же контент рендерится в два формата ещё при старте приложения (`functools.cache`, eager-загрузка в `lifespan`).
- **Единственный проект с настоящей сборкой фронтенда**: Tailwind компилируется pnpm-скриптами (`dev:css` с watch, `build:css` с minify) в статический `styles.css`. Никакого Play CDN.
- **Стилизация контента на сервере**: BeautifulSoup навешивает Tailwind-классы прямо на HTML-теги из Markdown (`a` → `text-sky-500 font-bold`, `h1`–`h6`, `blockquote`, `ul/ol`, `pre`) — CSS пишется один раз, а не в шаблонах.
- Изображения контента копируются в статику при старте, пути перезаписываются; `highlight.css` подключается лениво (`rel="preload"` → `stylesheet`) только при наличии блоков кода.
- Статика в production отдаётся мимо приложения — Caddy (`file_server /srv/static/`).

---

## 7. Сравнительный анализ: сходства и различия

### 7.1. Что общего у всех 6

1. **Нет SPA-фреймворков и бандлеров JS.** Ни React/Vue/Angular, ни webpack/Vite. Везде FastAPI + Jinja2 SSR + точечный vanilla JS.
2. **Jinja2 — единственный шаблонизатор во всех проектах**, с наследованием от `base.html` и блоками `title`/`content` (в fastapi-htmx-starter — `.jinja2`, у остальных — `.html`).
3. **Клиентский JS минимален и везде на vanilla JS**: от 17 строк (HabtNPMFastapiJinjaDemo) до одного файла редактора (diegolonio-dot-com) и inline-скриптов (остальные). Ни одного npm-пакета рантайма.
4. **Стили подключаются проще, чем можно ожидать от «современного» фронтенда**: либо CDN, либо self-hosted библиотека, либо ручной CSS. Полноценная сборка — только у luovkle.com (и только для CSS).
5. **Markdown — ключевой контент в 4 проектах** (AmiaBlog, diegolonio-dot-com, luovkle.com + админка), и везде это либо markdown-it (JS/Python), либо Python `markdown` — без единого общего решения.

### 7.2. Ключевая ось различий №1: где рендерится Markdown

| Подход | Проекты | Последствия |
|---|---|---|
| **На клиенте** | AmiaBlog | Сервер прост, но контент рендерится при каждой загрузке; нужен JS в браузере; `html: true` без санитизации |
| **На сервере, кэш в БД** | diegolonio-dot-com | HTML считается один раз при сохранении; быстрейшая отдача; доверенный автор (админ) |
| **На сервере, кэш в памяти** | luovkle.com | Всё считается при старте (+ ANSI-копия); мгновенный ответ, но инвалидация только рестартом |
| **Не применимо** | fastapi-htmx-starter, fastAPIuser-suren, HabtNPMFastapiJinjaDemo | Приложения без контента: CRUD/аутентификация/демо |

### 7.3. Ключевая ось различий №2: способ стилизации

| Подход | Проект | Оценка |
|---|---|---|
| Компонентная библиотека (веб-компоненты) + шрифты | AmiaBlog (MDUI v2) | Самый «богатый» UI, самодостаточный (self-hosted) |
| Ручной CSS без фреймворка | diegolonio-dot-com | Полный контроль, ноль зависимостей, но нет темизации |
| Tailwind **Play CDN** (компиляция в браузере) | fastapi-htmx-starter, HabtNPMFastapiJinjaDemo | Быстрый старт, но не для production (≈350 KB–3 MB JS, FOUC, CSP) |
| Bootstrap 5.3 CDN (только CSS + SRI) | fastAPIuser-suren | Классика; SRI — хорошая практика; JS-компоненты не используются |
| Tailwind **4 + локальная сборка (pnpm)** | luovkle.com | Единственный production-ready CSS-pipeline |

### 7.4. Ключевая ось различий №3: модель интерактивности

| Модель | Проект | Механизм |
|---|---|---|
| Частичные обновления DOM без JS-кода | **fastapi-htmx-starter** | HTMX: атрибуты `hx-*`, сервер возвращает HTML-фрагменты |
| Точечный fetch → JSON | fastAPIuser-suren, HabtNPMFastapiJinjaDemo | `fetch()` на JSON API, обновление текстового узла |
| Полноценный JS-инструмент (редактор) | diegolonio-dot-com | `editor.js`: preview через серверный рендер, загрузка изображений, chips |
| Веб-компоненты + WebSocket | AmiaBlog | MDUI-компоненты, live-preview через WS |
| Практически без JS | luovkle.com | Только copy-link |

### 7.5. Подсветка кода: три разных решения

- **highlight.js на клиенте** (AmiaBlog) — с серверной подготовкой: только нужные языки подключаются в шаблон.
- **Pygments на сервере** (diegolonio-dot-com, luovkle.com) — HTML блоков кода формируется заранее; CSS генерируется/подключается отдельно (`pygments.css` / `highlight.css` через `pygmentize`).

### 7.6. Математика и спецконтент

- Формулы LaTeX есть только в **diegolonio-dot-com**: сервер (`dollarmath_plugin`) готовит `\(...\)`, рендерит KaTeX в браузере (CDN). Остальные проекты формул не поддерживают.

### 7.7. Зрелость фронтенда (сводка)

| Критерий | AmiaBlog | diegolonio | htmx-starter | suren | HabtNPM | luovkle |
|---|---|---|---|---|---|---|
| Production-ready CSS | ✅ self-hosted | ✅ ручной CSS | ❌ Play CDN | ⚠️ CDN (SRI) | ❌ Play CDN | ✅ сборка pnpm |
| Сборка фронтенда | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ (Tailwind) |
| SEO | ✅ | ✅✅ (OG, Schema.org) | ⚠️ | ❌ | ❌ | ✅ |
| Доступность (a11y) | ⚠️ | ⚠️ | ⚠️ (ARIA нет) | ⚠️ (частично) | ❌ | ⚠️ |
| Объём клиентского JS | средний | малый (1 файл) | малый (inline) | малый (inline) | минимальный | минимальный |
| Кэширование контента | нет (рендер на клиенте) | ✅ в БД | — | — | — | ✅ в памяти |
| Уникальная фича | live-preview WS, статический сайт | KaTeX, админ-редактор | HTMX partial swap | SRI, email-шаблоны | образцовая структура шаблонов | HTML+ANSI по User-Agent |

---

## 8. Выводы

1. **Философия воркспейса единая — server-side rendering без SPA.** Все 6 проектов — FastAPI + Jinja2 + минимум vanilla JS. Это сознательный выбор: простота, SEO, быстрая первая загрузка.
2. **Различия — в трёх измерениях**: (а) где рендерится Markdown (клиент → БД-кэш → память), (б) чем стилизуется (веб-компоненты MDUI / ручной CSS / Tailwind CDN / Bootstrap CDN / Tailwind со сборкой), (в) как делается интерактивность (HTMX / fetch / WebSocket / почти ничего).
3. **Эталон production-подхода к CSS — luovkle.com** (локальная сборка Tailwind 4), в то время как три проекта (fastapi-htmx-starter, HabtNPMFastapiJinjaDemo, fastAPIuser-suren) зависят от CDN — это главный общий пункт из roadmap'ов.
4. **Эталон работы с контентом — diegolonio-dot-com** (рендер при сохранении + кэш HTML в БД) и **luovkle.com** (eager-рендер двух форматов при старте); AmiaBlog — противоположный полюс (рендер в браузере), оправданный его live-preview и статической генерацией.
5. **Общие точки роста для всех**: вынос inline-JS в статические файлы (CSP), добавление ARIA-атрибутов, favicon/OG-метатеги, отказ от CDN в пользу self-hosted/сборки.

---

## Приложение: источники по каждому проекту

| Проект | Основной документ |
|---|---|
| AmiaBlog | `my_blog_docs/AmiaBlog/docs/06_frontend_report.md` |
| diegolonio-dot-com | `my_blog_docs/diegolonio-dot-com/docs/frontend_report.md` |
| fastapi-htmx-starter | `my_blog_docs/fastapi-htmx-starter/docs/07_frontend.md` |
| fastAPIuser-suren | `my_blog_docs/fastAPIuser-suren/docs/06_frontend_bootstrap_analysis.md` |
| HabtNPMFastapiJinjaDemo | `my_blog_docs/HabtNPMFastapiJinjaDemo/docs/06_frontend.md` (+ `05_tailwind_cdn_vs_production.md`) |
| luovkle.com | `my_blog_docs/luovkle.com/docs/05_markdown_rendering_report.md` (+ `02_architecture.md`) |
