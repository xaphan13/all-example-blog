# AmiaBlog: отчёт по фронтенду

## Общая архитектура фронтенда

Фронтенд AmiaBlog — это классический server-side рендеринг с небольшим слоем клиентского JavaScript. FastAPI на сервере собирает HTML из Jinja2-шаблонов, минифицирует его через `htmlmin` и отдаёт браузеру. Вся интерактивность реализована на веб-компонентах **MDUI v2** и небольших inline-скриптах; никаких фреймворков вроде React или Vue не используется.

### Основные активы в `static/`

| Файл / директория | Назначение |
|---|---|
| `static/mdui_2.1.4/mdui.css` | Стили Material Design You. |
| `static/mdui_2.1.4/mdui.global.js` | Глобальная сборка MDUI: регистрирует кастомные элементы `mdui-*`. |
| `static/roboto/` | Шрифт Roboto и CSS с `@font-face`. |
| `static/material_icons/` | Иконочный шрифт Material Icons. |
| `static/markdown-it-14.1.0.min.js` | Парсер Markdown на клиенте. |
| `static/markdown-it-footnote-4.0.0.min.js` | Плагин сносок для markdown-it. |
| `static/hljs_11.1.1/highlight.min.js` | Ядро highlight.js. |
| `static/hljs_11.1.1/amiablog.min.css` | Тема подсветки кода. |
| `static/hljs_11.1.1/{lang}.min.js` | Языковые бандлы, скачанные сервером при старте. |
| `static/live_preview.js` | Клиент WebSocket для live-preview. |
| `static/favicon.ico` | Иконка сайта. |

## Поток рендеринга страницы

```
HTTP-запрос
   │
   ▼
FastAPI route (main.py)
   │
   ▼
TemplateRenderer.render_to_plain_text()
   │
   ├─► Jinja2 merge контекста + static_params
   ├─► htmlmin.minify()
   │
   ▼
HTMLResponse
   │
   ▼
Браузер
   │
   ├─► загружает MDUI, шрифты, иконки
   ├─► выполняет inline-скрипты шаблона
   ├─► (на странице поста) markdown-it рендерит Markdown
   └─► (при наличии блоков кода) highlight.js подсвечивает синтаксис
```

## Базовый шаблон `templates/base.html`

Все страницы наследуют `base.html`. Он отвечает за:

- `<html lang="{{ config.site_language }}" class="mdui-theme-{{ config.site_settings.theme }}">` — язык и тема.
- SEO-метатеги `description`, `keywords`, `theme-color`.
- Опционный скрипт Cloudflare Analytics (`config.cloudflare_analytics_token`).
- Подключение `mdui.css`, `mdui.global.js`, `roboto.css`, `material_icons.css`.
- Блоки для наследования:
  - `meta_description`, `meta_keywords`
  - `head_extra` — дополнительные `<script>` / `<style>` в `<head>`.
  - `title` — заголовок вкладки.
  - `content` — основное содержимое.
  - `copyright` — футер с лицензией.
  - `extra_scripts` — скрипты перед закрывающим `</body>`.
- Навигационный drawer и top-app-bar.
- Диалог «О сайте» с версией, коммитом и общим числом постов.

### Переключение динамических и статических URL

В `static_params` передаётся флаг `is_static`. В `base.html` и других шаблонах он используется для добавления суффикса `.html`:

```jinja2
<a href="/tags{% if is_static %}.html{% endif %}">...</a>
```

Поиск (`/search`) и live-preview в статическом режиме не доступны, поэтому соответствующие элементы навигации скрыты.

## Рендеринг Markdown

Сервер не превращает Markdown в HTML. В `Post.content` хранится сырой Markdown, который передаётся в шаблон `templates/post.html`.

### Как это работает в `templates/post.html`

1. В `<head>` подключаются библиотеки:
   ```html
   <script src="/static/markdown-it-14.1.0.min.js"></script>
   <script src="/static/markdown-it-footnote-4.0.0.min.js"></script>
   ```

2. В теле страницы Markdown размещён в скрытом блоке:
   ```html
   <pre style="display: none;" id="post-content">{{ post.content }}</pre>
   ```
   Jinja2 с `select_autoescape()` экранирует HTML-сущности в содержимом.

3. Inline-скрипт в `extra_scripts`:
   ```javascript
   function unescapeHtml(escapedStr) {
       var elem = document.createElement('textarea');
       elem.innerHTML = escapedStr;
       return elem.value;
   }

   function renderPage(){
     const md = window.markdownit({
       html: true,
       linkify: true,
       typographer: true,
       breaks: true
     }).use(window.markdownitFootnote);

     const result = md.render(unescapeHtml(mdui.$('#post-content')[0].innerHTML));
     mdui.$('#markdown-render-result')[0].innerHTML = result;
   }

   renderPage();
   window._amiablog_renderPage = renderPage;
   ```

4. Функция `unescapeHtml` превращает HTML-сущности обратно в исходные символы, чтобы `markdown-it` получил чистый Markdown.

5. `markdown-it` с параметром `html: true` позволяет вставлять произвольный HTML внутри Markdown. Это даёт авторам гибкость, но перекладывает ответственность за безопасность на автора контента: сервер не санитизирует результат.

6. Результат записывается в `<div id="markdown-render-result" class="mdui-prose">`.

### Стили для Markdown-контента

В `templates/post.html` внутри `head_extra` определены дополнительные стили:

- `<pre>` и `<code>` получают цвет фона из MDUI-переменных и горизонтальную прокрутку.
- Таблицы также имеют `overflow-x: auto`, чтобы не ломать вёрстку на узких экранах.
- Класс `mdui-prose` от MDUI задаёт типографику для заголовков, списков, цитат и т.д.

## Подсветка синтаксиса

### Определение языков

Сервер (`core/hljs.py`) сканирует `post.content` на наличие блоков кода, начинающихся с ` ```<lang>`. В шаблон передаётся список `hljs_languages` — пересечение найденных языков и тех, что указаны в `config.json` в `site_settings.hljs_languages` и уже скачаны в `static/hljs_11.1.1/`.

### Подключение в `templates/post.html`

```jinja2
{% if hljs_languages %}
<link rel="stylesheet" href="/static/hljs_11.1.1/amiablog.min.css">
<script src="/static/hljs_11.1.1/highlight.min.js"></script>
{% for language in hljs_languages %}
<script src="/static/hljs_11.1.1/{{ language }}.min.js"></script>
{% endfor %}
{% endif %}
```

После рендеринга Markdown вызывается:

```javascript
{% if hljs_languages %}
<script>hljs.highlightAll();</script>
{% endif %}
```

## Компоненты MDUI и клиентская логика

### Основные используемые компоненты

- `mdui-navigation-drawer` — боковое меню.
- `mdui-top-app-bar` — верхняя панель.
- `mdui-list` / `mdui-list-item` — пункты меню.
- `mdui-card` — карточки постов.
- `mdui-chip` — теги.
- `mdui-button-icon` — иконки-кнопки.
- `mdui-select` / `mdui-menu-item` — выпадающий список сортировки.
- `mdui-text-field` — поле поиска.
- `mdui-button` — кнопка отправки формы.
- `mdui-dialog` — диалог «О сайте».
- `mdui-tooltip` — подсказки для тегов.
- `mdui-circular-progress` — индикатор на странице ошибки.
- `mdui-icon` — Material-иконки.
- `mdui-prose` — стилизованный текст.

### Типовые inline-скрипты

- `base.html`: `toggleSideNav()` переключает drawer; `mdui.setColorScheme('{{ config.site_settings.color_scheme }}')` задаёт акцентный цвет.
- `posts.html`: `updateOrder(order)` меняет GET-параметр `?order=` и перезагружает страницу.
- `error.html`: обратный отсчёт 5 секунд с прогресс-баром, затем `window.history.back()`.
- `post.html`: рендеринг Markdown и live-preview context.

## Живое превью (`live_preview`)

Включено только при `config.live_preview = true`.

### Серверная часть

`core/live_preview.py` и маршрут `/api/live-preview-ws` в `main.py`.

### Клиентская часть

`templates/post.html` подключает `/static/live_preview.js`, если live-preview включён:

```jinja2
{% if config.live_preview %}
<script>
window._amiablog_slug = "{{ post.slug }}"
window._amiablog_i18n_ctx = { ... }
</script>
<script src="/static/live_preview.js"></script>
{% endif %}
```

`static/live_preview.js`:

1. Открывает WebSocket на `ws(s)://<host>/api/live-preview-ws`.
2. После открытия отправляет `{"type": "subscribe", "slug": window._amiablog_slug}`.
3. Обрабатывает сообщения:
   - `update` — заменяет содержимое `#post-content` на новый Markdown и вызывает `window._amiablog_renderPage()`.
   - `refresh` — перезагружает страницу (нужно при изменении метаданных, которые рендерятся сервером).
   - `pong` — heartbeat.
4. Каждые 5 секунд отправляет `ping`.
5. При ошибке/закрытии показывает `mdui.alert()` с текстом из i18n.

## Формы и навигация

### Поиск

`templates/search.html` содержит обычную HTML-форму:

```html
<form action="/search" method="GET">
    <mdui-text-field name="query" ...></mdui-text-field>
    <mdui-select name="order">...</mdui-select>
    <mdui-button type="submit">...</mdui-button>
</form>
```

Сервер (`main.py`, `/search`) валидирует параметры и возвращает ту же страницу с результатами.

### Сортировка постов

`templates/posts.html` использует `<mdui-select onchange="updateOrder(this.value)">`. Изменение значения обновляет query string и перезагружает страницу. В статическом режиме селект скрыт, потому что сортировка на стороне сервера недоступна.

### Теги и URL

Теги — это произвольные строки, поэтому в шаблонах применяется фильтр `urlencode`:

```jinja2
<mdui-chip href="/tag/{{ tag | urlencode }}{% if is_static %}.html{% endif %}">{{ tag }}</mdui-chip>
```

## Особенности статического режима

`staticify.py` генерирует HTML-файлы для каждой страницы. В шаблонах учитывается `is_static = True`:

- Ссылки на страницы получают `.html`.
- `/feed` превращается в `/feed.xml`.
- Поиск и live-preview не рендерятся в навигации.
- Каждый пост сохраняется как `post/<slug>.html` и `post/<slug>.md`.

## Производительность и ограничения

- HTML минифицируется сервером (`htmlmin`).
- Jinja2-кэш шаблонов включён в production (`disable_template_cache=false`).
- Markdown рендерится заново на каждой загрузке страницы поста — приемлемо для небольшого блога, но не оптимально для очень больших постов.
- Нет Service Worker, prefetch, lazy-loading изображений или бандлеров фронтенда.
- `markdown-it` с `html: true` требует доверия к авторам постов; встроенной защиты от XSS в Markdown-контенте нет.
