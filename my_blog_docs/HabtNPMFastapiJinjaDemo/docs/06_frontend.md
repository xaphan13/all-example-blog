# 06_frontend.md
# Отчёт по фронтенду

## Обзор

Фронтенд проекта построен по принципу **server-side rendering (SSR)**: вся HTML-разметка генерируется на сервере через Jinja2, а клиентский JavaScript используется точечно — только для интерактивного вызова JSON API. Стилистика — **Tailwind CSS через CDN** (utility-first классы прямо в разметке, без этапа сборки).

Ключевые характеристики:

| Аспект | Реализация |
|---|---|
| Рендеринг | Полностью серверный (Jinja2 3.1.6) |
| Стили | Tailwind CSS через CDN + небольшой собственный CSS |
| Клиентский JS | Один файл `static/js/main.js`, vanilla JS, без фреймворков |
| Сборка | Отсутствует (нет `package.json`, `node_modules`) |
| Зависимости фронтенда | Единственная — CDN-скрипт Tailwind |
| SPA-фреймворки | Не используются |

---

## Карта фронтенд-файлов

```
templates/
├── base.html            # Базовый layout: <head>, Tailwind CDN, каркас страницы
├── partials/
│   ├── navbar.html      # Шапка с навигацией
│   └── footer.html      # Подвал
└── pages/
    ├── index.html       # Главная: hero, карточки features, кнопка Ping
    └── about.html       # Страница «О проекте»: описание и структура

static/
├── css/
│   └── style.css        # Собственный CSS поверх Tailwind (7 строк)
└── js/
    └── main.js          # Клиентская логика: fetch /api/ping (17 строк)
```

| Файл | Строк | Ответственность |
|---|---|---|
| `templates/base.html` | 26 | Общий каркас всех страниц, подключение Tailwind, CSS, JS |
| `templates/partials/navbar.html` | 9 | Навигационная панель (header + nav) |
| `templates/partials/footer.html` | 5 | Подвал |
| `templates/pages/index.html` | 27 | Контент главной страницы |
| `templates/pages/about.html` | 23 | Контент страницы «О проекте» |
| `static/css/style.css` | 7 | Глобальный шрифт для `<code>` |
| `static/js/main.js` | 17 | Обработчик клика по кнопке Ping |

Суммарный объём фронтенд-кода — **около 115 строк**. Это сознательный минимум: проект демонстрирует архитектуру backend'а.

---

## Слой шаблонов

### Схема наследования

```
base.html  (layout: <head>, navbar, main, footer, script)
   ▲
   ├── {% extends %}          {% extends %}
   │                          │
index.html                 about.html
(блоки title, content)     (блоки title, content)
```

- `base.html` определяет два переопределяемых блока: `title` и `content`.
- Страницы не содержат `<head>`, подключения стилей или скриптов — всё это в одном месте.
- Партиалы `navbar.html` и `footer.html` подключаются в `base.html` через `{% include %}`.

### Контекст шаблонов

| Переменная | Откуда берётся | Где используется |
|---|---|---|
| `app_name` | Глобальная переменная Jinja2 (`core/templating.py`) | `base.html` (title по умолчанию), `navbar.html` (логотип-ссылка), `index.html`/`about.html` (суффикс title) |
| `title` | Context из обработчика (`routers/pages.py`) | Блок `title` и заголовок `about.html` |
| `features` | Context из `routers/pages.py::index` | Цикл `{% for %}` в `index.html` |

Глобальная переменная задаётся один раз в `core/templating.py`:

```python
templates.env.globals["app_name"] = settings.app_name
```

Благодаря этому ни один обработчик не передаёт `app_name` вручную, а название приложения меняется в одном месте (`APP_NAME` в конфиге) и сразу отражается во всех шаблонах.

### Рендеринг (современный API)

Обработчики используют актуальную сигнатуру — `request` первым аргументом:

```python
templates.TemplateResponse(request, "pages/index.html", {"title": "Главная", "features": features})
```

Старая форма `TemplateResponse("name.html", {"request": request, ...})` не используется — она помечена устаревшей в Starlette.

### Пайплайн рендеринга страницы

```
Обработчик (routers/pages.py)
   │  TemplateResponse(request, "pages/index.html", {...})
   ▼
Jinja2 загружает pages/index.html
   │  {% extends "base.html" %}
   ▼
Подстановка блоков title / content в base.html
   ▼
Выполнение {% include "partials/navbar.html" %} и {% include "partials/footer.html" %}
   ▼
Подстановка {{ app_name }} из env.globals
   ▼
Готовый HTML → ответ 200, Content-Type: text/html
```

---

## Разметка и верстка

### Каркас страницы (`base.html`)

```html
<body class="h-full flex flex-col bg-slate-50 text-slate-800">
    {% include "partials/navbar.html" %}
    <main class="flex-1 max-w-3xl w-full mx-auto px-4 py-10">
        {% block content %}{% endblock %}
    </main>
    {% include "partials/footer.html" %}
    <script src=".../js/main.js"></script>
</body>
```

- **Sticky-footer layout**: `body` — flex-колонка на всю высоту (`h-full flex flex-col`), `main` растягивается через `flex-1`, поэтому подвал всегда прижат к низу страницы, даже когда контента мало.
- **Контентная колонка**: `max-w-3xl mx-auto` — читабельная ширина (~768px), центрированная, с боковыми отступами `px-4`.
- **Подключение скрипта** — в конце `<body>`, без `defer`: DOM к моменту выполнения уже построен.

### Навигация (`partials/navbar.html`)

- `<header>` с белым фоном и нижней границей (`border-b border-slate-200`), высота фиксированная — `h-14`.
- Логотип — ссылка на `/` с названием приложения (`{{ app_name }}`), акцентный цвет `text-indigo-600`.
- Две ссылки: «Главная» и «О проекте», hover-эффект через `hover:text-indigo-600 transition-colors`.
- Выравнивание: `flex items-center justify-between` — логотип слева, ссылки справа.

### Главная страница (`index.html`)

Три секции:

1. **Hero** — заголовок `h1` (`text-3xl font-bold`) и подзаголовок, выравнивание по центру.
2. **Карточки features** — CSS Grid: `grid gap-4 sm:grid-cols-3`. На мобильных — одна колонка, от брейкпоинта `sm` (640px) — три. Карточки генерируются циклом по кортежам `(name, description)`, переданным из обработчика. Стиль карточки: белый фон, скругление `rounded-xl`, тонкая граница, лёгкая тень `shadow-sm`.
3. **Кнопка Ping** — `id="ping-btn"` (зацепка для JS) и пустой `<p id="ping-result">`, куда скрипт выводит результат.

### Страница «О проекте» (`about.html`)

Одна карточка-статья с заголовком, описанием и списком структуры проекта. Инлайн-код выделен через `<code>` с акцентным цветом.

### Адаптивность

| Приём | Где |
|---|---|
| Viewport meta | `base.html`: `width=device-width, initial-scale=1.0` |
| Grid → одна колонка на мобильных | `index.html`: `grid ... sm:grid-cols-3` |
| Относительные размеры текста | Tailwind-классы `text-sm`, `text-2xl`, `text-3xl` |
| Flex-обёртка контента | `px-4` везде, без фиксированных ширин |

Верстка адаптивна «из коробки» Tailwind: единственный использованный брейкпоинт — `sm:`.

---

## Стили

### Tailwind через CDN

В `base.html`:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

Это полноценный компилятор Tailwind, работающий в браузере: он сканирует DOM, находит utility-классы и генерирует CSS на лету, вставляя его в `<style>` на странице.

**Почему так в этом проекте:** демо ориентировано на backend-архитектуру; CDN убирает `package.json`, `node_modules` и шаг компиляции CSS. Подробный разбор компромиссов (размер, FCP/LCP, CSP, кэширование) и пошаговый план миграции на production-сборку — в [05_tailwind_cdn_vs_production.md](05_tailwind_cdn_vs_production.md).

### Используемые классы Tailwind

| Группа | Классы |
|---|---|
| Layout | `h-full`, `flex`, `flex-col`, `flex-1`, `grid`, `mx-auto`, `max-w-3xl`, `w-full`, `px-4`, `py-10`, `h-14`, `justify-between`, `items-center`, `justify-center` |
| Spacing | `mt-2`, `mt-3`, `mt-4`, `mt-6`, `mt-10`, `p-5`, `p-6`, `gap-4`, `gap-6`, `space-y-1` |
| Типографика | `text-sm`, `text-2xl`, `text-3xl`, `font-semibold`, `font-bold`, `font-medium`, `text-center`, `list-disc`, `list-inside` |
| Цвета | `bg-slate-50`, `bg-white`, `text-slate-800`, `text-slate-900`, `text-slate-600`, `text-slate-500`, `text-indigo-600`, `bg-indigo-600`, `text-white`, `hover:text-indigo-600`, `hover:bg-indigo-700` |
| Границы и эффекты | `border-b`, `border-t`, `border-slate-200`, `rounded-xl`, `rounded-lg`, `shadow-sm`, `transition-colors` |

Палитра единообразна: нейтральные оттенки `slate` + один акцентный цвет `indigo`.

### Собственный CSS (`static/css/style.css`)

```css
code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
```

Единственное правило — системный моноширинный стек для `<code>`. Подключается после Tailwind-скрипта, поэтому при конфликте приоритет у этого файла (обычный каскад: позднее правило с той же специфичностью побеждает).

Подключение статики через `url_for`:

```html
<link rel="stylesheet" href="{{ url_for('static', path='css/style.css') }}">
```

---

## Клиентский JavaScript (`static/js/main.js`)

### Логика

```js
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("ping-btn");
    const result = document.getElementById("ping-result");
    if (!button || !result) return;          // защита: скрипт на всех страницах

    button.addEventListener("click", async () => {
        result.textContent = "Запрос...";    // промежуточный статус
        try {
            const response = await fetch("/api/ping");
            const data = await response.json();
            result.textContent = `Ответ: ${data.status} — ${data.message}`;
        } catch (error) {
            result.textContent = "Ошибка запроса";
        }
    });
});
```

### Разбор по шагам

1. **Инициализация** — подписка на `DOMContentLoaded`; скрипт подключён в конце `<body>`, так что к моменту выполнения DOM гарантированно готов.
2. **Поиск элементов** — по `id`: `#ping-btn` и `#ping-result`. Проверка `if (!button || !result) return` делает скрипт безопасным для подключения на всех страницах (на `/about` этих элементов нет — скрипт просто выходит).
3. **Обработка клика** — async-обработчик:
   - сразу показывает статус «Запрос...» (обратная связь пользователю);
   - `fetch("/api/ping")` — относительный путь, работает на любом хосте без CORS-настройки (страница и API на одном origin);
   - `response.json()` — парсинг JSON-ответа `{"status": "ok", "message": "pong"}`;
   - результат выводится в `#ping-result` через шаблонную строку.
4. **Обработка ошибок** — `try/catch`: сетевая ошибка или невалидный JSON выводят «Ошибка запроса».

### Особенности

| Аспект | Оценка |
|---|---|
| Зависимости | Нет — vanilla JS, ноль библиотек |
| HTTP-статус | Не проверяется (`response.ok`) — ответ 4xx/5xx с JSON-телом попадёт в «успешную» ветку |
| Состояние кнопки | Во время запроса кнопка остаётся активной — возможны повторные клики |
| Совместимость | `fetch`, `async/await`, template literals — все современные браузеры |

---

## Поток данных фронтенда

### Статический сценарий (рендеринг страницы)

```
Браузер: GET /
   ▼
FastAPI → routers/pages.py::index → Jinja2 → HTML
   ▼
Браузер парсит HTML:
   ├─► <script cdn.tailwindcss.com> → генерация CSS на клиенте
   ├─► GET /static/css/style.css    → StaticFiles
   └─► GET /static/js/main.js       → StaticFiles
   ▼
Страница отрисована
```

### Динамический сценарий (кнопка Ping)

```
Клик по #ping-btn
   ▼
fetch("GET /api/ping")        ← тот же origin, CORS не нужен
   ▼
routers/api.py::ping → {"status": "ok", "message": "pong"}
   ▼
main.js: data.status + data.message → textContent #ping-result
```

Данные с сервера попадают на страницу двумя путями: **при рендеринге** (context шаблона: `title`, `features`, `app_name`) и **после загрузки** (JSON через `fetch`). Гибридный SSR + точечный API — типичная схема для классических серверных приложений.

---

## Оценка качества фронтенда

### Сильные стороны

| Аспект | Комментарий |
|---|---|
| DRY на уровне разметки | Ни один шаблон не дублирует `<head>`, navbar или footer — всё в `base.html` и партиалах |
| Единая точка настройки Jinja2 | Глобальные переменные и путь к шаблонам — в `core/templating.py` |
| Актуальный API | `TemplateResponse(request, ...)` — без deprecation-предупреждений |
| Разделение ответственности | Разметка — в шаблонах, стили — в CSS/Tailwind, поведение — в JS |
| Адаптивность | Работает на мобильных без отдельной мобильной вёрстки |
| Минимализм | ~115 строк фронтенда, ноль зависимостей, ноль сборки |
| Идемпотентная зацепка JS | Скрипт подключается на всех страницах, но не падает там, где нет кнопки |

### Слабые места и рекомендации

| # | Проблема | Риск | Рекомендация |
|---|---|---|---|
| 1 | Tailwind через CDN | ~3 МБ CSS генерируется на клиенте при каждой загрузке; несовместим со строгим CSP; нет офлайна | Для production — локальная сборка (план в `docs/05_tailwind_cdn_vs_production.md`) |
| 2 | Активная навигация не подсвечивается | Пользователь не видит, на какой странице находится | Передавать в шаблон имя текущего маршрута и подсвечивать ссылку условным классом |
| 3 | `fetch` не проверяет `response.ok` | Ошибки 4xx/5xx с JSON-телом показываются как успешный ответ | Добавить `if (!response.ok) throw new Error(...)` |
| 4 | Кнопка не блокируется на время запроса | Возможны дублирующие запросы при быстрых кликах | `button.disabled = true` до завершения `fetch` |
| 5 | Ошибка `fetch` не логируется | `catch (error)` глотает объект ошибки — сложно отлаживать | `console.error(error)` в catch-блоке |
| 6 | Нет `<meta name="description">`, OG-тегов, favicon | Слабое SEO и отсутствие иконки вкладки | Добавить в `base.html` блок `meta` с возможностью переопределения на страницах |
| 7 | Нет `aria`-атрибутов и `:focus`-стилей | Доступность: навигация с клавиатуры и скринридеры | `aria-current="page"` для активной ссылки, focus-стили Tailwind (`focus-visible:...`) |
| 8 | Статика без cache-control | `style.css` и `main.js` запрашиваются заново при каждом визите | Настроить заголовки кэширования или версионирование (`style.css?v=1`) |
| 9 | Дублирование паттерна `title · {{ app_name }}` | Мелочь, но при росте числа страниц — повтор | Вынести суффикс в `base.html`: `{% block title %}{{ title }} · {{ app_name }}{% endblock %}` и передавать только `title` |

### Итоговая оценка

Фронтенд соответствует назначению проекта — **демонстрация серверного рендеринга с минимальным клиентом**. Архитектура шаблонов (наследование + партиалы + глобальный контекст) масштабируема: добавление новой страницы не требует трогать существующие файлы. Основной долг — не в структуре, а в «демо-режиме» Tailwind CDN и отсутствии полировки UX (активная навигация, обработка ошибок fetch, мета-теги); все пункты локальны и не требуют переделки архитектуры.

# End of 06_frontend.md
