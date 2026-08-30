# Отчёт по фронтенду diegolonio.com

## 1. Общая концепция

Фронтенд сайта `diegolonio.com` — это классический серверный рендеринг (SSR) без использования frontend-фреймворков. Всё HTML-наполнение формируется на стороне сервера через FastAPI + Jinja2, а в браузер отдаётся готовый HTML с небольшим количеством ванильного JavaScript и CSS.

Основные принципы:

- **Никаких React/Vue/Angular** — только серверные шаблоны Jinja2.
- **Минимум JavaScript** — единственный значимый скрипт `editor.js` для админ-редактора.
- **Минимум CSS-фреймворков** — стили написаны вручную в `app/static/css/`.
- **Внешние CDN** используются только для иконок (Font Awesome), значков технологий (devicon), KaTeX для формул и shields.io для бейджей.

---

## 2. Архитектура фронтенда

```
Браузер
   │ HTTP-запрос
   ▼
FastAPI (app/main.py)
   │
   ├── public router (app/routers/public.py)  → публичные страницы
   ├── admin router (app/routers/admin.py)    → админ-панель
   │
   ▼
Jinja2Templates (app/templating.py)
   │
   ├── app/templates/base.html                → базовый layout
   ├── app/templates/*.html                   → страницы
   └── app/templates/admin/*.html             → шаблоны админки
   │
   ▼
HTML-ответ + статика
   │
   ├── /static/css/*.css                      → стили
   ├── /static/js/editor.js                   → редактор
   ├── /static/img/*                          → изображения сайта
   └── /media/*                               → загруженные пользователем изображения
```

### 2.1. Шаблонизация Jinja2

Централизованный экземпляр шаблонов создаётся в `app/templating.py`:

```python
templates = Jinja2Templates(directory="app/templates")
```

В нём регистрируются:

- **Глобальная переменная `base_url`** — домен сайта из `.env`.
- **Глобальная переменная `static_v`** — timestamp запуска сервера, используется как query-параметр `?v=` для сброса кэша статики после деплоя.
- **Фильтр `dateformat`** — форматирует `datetime` в вид `July 9, 2026`.

### 2.2. Наследование шаблонов

- Все страницы наследуют `base.html`.
- Шаблоны админки наследуют `admin/base_admin.html`, который в свою очередь наследует `base.html`.
- Переиспользуемый partial `_post_cards.html` включается в `index.html`, `tag.html`, `search.html`.

### 2.3. Блоки в base.html

| Блок | Назначение |
|------|------------|
| `title` | Заголовок страницы |
| `description` | Meta description |
| `og_type` | OpenGraph type |
| `og_image` | OpenGraph image |
| `extra_head` | Дополнительные стили/скрипты |
| `wrapper_class` | Класс для `.wrapper` |
| `content` | Основной контент страницы |

---

## 3. Публичные страницы

### 3.1. Главная (`index.html`)

- Приветственный блок с кратким описанием автора.
- Сетка карточек постов (`_post_cards.html`).
- Пагинация по 6 постов на страницу (`POSTS_PER_PAGE = 6`).
- Структурированные данные Schema.org (`WebSite`) для поисковиков.

### 3.2. Страница поста (`post.html`)

- Заголовок, дата публикации, теги.
- Основной контент: `{{ post.content_html | safe }}` — HTML, сформированный из markdown на сервере.
- Навигация к предыдущему/следующему посту.
- Подключение KaTeX для рендеринга формул на клиенте.
- Стили `post.css` + `pygments.css`.

### 3.3. Страница о себе (`about.html`)

- Статический текст биографии.
- Tech stack в виде бейджей от shields.io.
- Список проектов, загружаемых из `projects.yaml` через `app/projects.py`.
- Иконки из devicon и Font Awesome.

### 3.4. Поиск (`search.html`) и теги (`tag.html`)

- Используют общий partial `_post_cards.html`.
- Поиск работает через PostgreSQL full-text search.

### 3.5. Служебные страницы

- `404.html` — кастомная страница ошибки.
- `robots.txt` — генерируется в `public.py`.
- `sitemap.xml` — генерируется в `public.py` из всех опубликованных постов.

---

## 4. Стилизация

### 4.1. Файлы CSS

| Файл | Назначение |
|------|------------|
| `base.css` | Базовые стили, layout, header, footer, навигация |
| `home.css` | Главная страница, карточки постов, пагинация |
| `post.css` | Стили контента поста (типографика, списки, изображения, видео) |
| `about.css` | Страница about, tech stack, project grid |
| `search.css` | Страница поиска |
| `pygments.css` | Подсветка синтаксиса кода |
| `admin/admin.css` | Базовые стили админки |
| `admin/login.css` | Страница входа |
| `admin/manager.css` | Список постов в админке |
| `admin/editor.css` | Markdown-редактор |

### 4.2. Особенности

- CSS написан вручную, без препроцессоров.
- Все ссылки на собственные CSS/JS включают `?v={{ static_v }}` для cache busting.
- Подсветка кода использует классы Pygments, которые определяются в `pygments.css`.
- Тёмная/светлая тема не предусмотрена — один фиксированный набор стилей.

---

## 5. JavaScript

Весь клиентский JavaScript находится в одном файле `app/static/js/editor.js`.

### 5.1. Что делает editor.js

Редактор постов в админ-панели:

1. **Переключение Edit / Preview**
   - Tab Edit показывает textarea с markdown.
   - Tab Preview отправляет markdown на сервер (`POST /admin/api/preview`), получает HTML и отображает его.
   - После получения HTML вызывается KaTeX `renderMathInElement` для формул.

2. **Загрузка изображений**
   - Drag & drop или paste изображения в textarea.
   - Изображение отправляется на `POST /admin/api/images`.
   - В текст вставляется markdown-ссылка `![alt](/media/uuid.ext)`.

3. **Обложка поста (cover image)**
   - Поле для ввода URL или загрузки файла.
   - Загруженное изображение отображается в виде chip с preview по наведению.

4. **Tags как chips**
   - Ввод тегов через текстовое поле.
   - Enter или запятая превращает текст в chip.
   - Backspace в пустом поле удаляет последний chip.
   - Скрытое поле `tags` хранит теги в формате `tag1, tag2` для отправки на сервер.

5. **Auto-resize summary**
   - Высота поля summary автоматически подстраивается под содержимое.

### 5.2. Почему так мало JavaScript

Сайт сознательно минималистичен: основной контент — это статьи с текстом, кодом и формулами. Вся навигация, пагинация, поиск и рендеринг постов происходят на сервере.

---

## 6. Как рендерится Markdown

Markdown рендерится не в браузере, а **на сервере** при сохранении поста. Готовый HTML кешируется в базе данных в поле `posts.content_html`. Публичные страницы выводят этот HTML напрямую через `| safe`.

### 6.1. Pipeline рендеринга

Файл: `app/markdown_render.py`

```
Markdown-исходник (content_md)
   │
   ▼
markdown-it-py (commonmark + html + table + strikethrough)
   │
   ├── dollarmath_plugin  → обрабатывает $...$ и $$...$$
   ├── Pygments           → подсветка блоков ```
   └── raw HTML           → пропускается как есть
   │
   ▼
HTML (content_html)
   │
   ▼
сохраняется в PostgreSQL
```

### 6.2. Конфигурация парсера

```python
_md = MarkdownIt("commonmark", {"html": True, "highlight": _highlight})
_md.enable(["table", "strikethrough"])
_md.use(dollarmath_plugin, allow_labels=False, double_inline=True)
```

- `html: True` — разрешён raw HTML (например, `<video>`, YouTube iframe). Безопасно, потому что писать посты может только администратор.
- `table` — таблицы.
- `strikethrough` — зачёркивание.

### 6.3. Подсветка кода

Функция `_highlight` использует Pygments:

```python
def _highlight(code: str, lang: str, attrs: str) -> str:
    lexer = get_lexer_by_name(lang) if lang else TextLexer()
    html = pygments_highlight(code, lexer, _formatter)
    return html
```

- Автоматическая нумерация строк (`linenos="inline"`).
- Если язык неизвестен — используется `TextLexer` (только номера строк без цвета).
- Внешний `<div class="highlight">` обрезается, остаётся только `<pre>`.

### 6.4. Математические формулы

Плагин `dollarmath_plugin` обрабатывает:

- `$...$` — inline math.
- `$$...$$` — block math.

Кастомные render-правила преобразуют их в разметку для KaTeX:

```python
def _math_inline(self, tokens, idx, options, env):
    return f"\\({escape(tokens[idx].content)}\\)"

def _math_block(self, tokens, idx, options, env):
    return f'<div class="math-block">\\[{escape(tokens[idx].content)}\\]</div>\n'
```

То есть сервер НЕ рендерит формулы в HTML — он только сохраняет LaTeX внутри `\(...\)` и `\[...\]`. Финальный рендеринг выполняет KaTeX в браузере.

### 6.5. Клиентский рендеринг KaTeX

В `post.html` и `admin/form.html` подключаются:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
        ],
        throwOnError: false
    });">
</script>
```

`auto-render` находит формулы в готовом HTML и заменяет их на отрендеренные SVG/HTML.

### 6.6. Preview в редакторе

Когда автор нажимает "Preview" в админке:

1. `editor.js` отправляет текущий markdown на `POST /admin/api/preview`.
2. Сервер вызывает тот же `render_markdown()`, что и при сохранении.
3. Возвращается HTML, который вставляется в `<div id="preview">`.
4. Если KaTeX уже загружен, вызывается `renderMathInElement(preview, ...)`.

Так автор видит точно такой же результат, какой будет опубликован.

### 6.7. Куда сохраняется HTML

При создании/обновлении поста в `app/routers/admin.py`:

```python
posts.create(
    db, slug, title, summary, cover_image or None,
    content_md, render_markdown(content_md), published,
)
```

`content_md` — исходный markdown, `render_markdown(content_md)` — готовый HTML. Оба хранятся в БД. Публичная страница поста использует только `content_html`:

```html
{{ post.content_html | safe }}
```

---

## 7. Жизненный цикл запроса страницы поста

```
GET /post/{slug}
   │
   ▼
app/routers/public.py::post_detail
   │
   ├── SELECT * FROM posts WHERE slug = %s AND published = true
   ├── SELECT tags JOIN post_tags WHERE post_id = ...
   ├── SELECT предыдущий пост ORDER BY published_at DESC
   └── SELECT следующий пост ORDER BY published_at ASC
   │
   ▼
Jinja2: app/templates/post.html
   │
   ├── base.html → layout, OG-мета, CSS
   ├── post.css + pygments.css
   └── KaTeX CDN
   │
   ▼
HTML-ответ
   │
   ▼
Браузер
   ├── Парсит HTML
   ├── Загружает CSS, изображения
   ├── Загружает KaTeX
   └── KaTeX renderMathInElement рендерит формулы
```

---

## 8. Внешние зависимости фронтенда

| Ресурс | Использование | Файлы |
|--------|---------------|-------|
| Font Awesome 6.5.1 | Иконки в header/footer | `base.html` |
| KaTeX 0.16.9 | Рендеринг LaTeX-формул | `post.html`, `admin/form.html` |
| devicon | Иконки технологий на about | `about.html` |
| shields.io | Бейджи технологий | `about.html` |

---

## 9. Особенности и ограничения

### 9.1. Плюсы подхода

- **Простота** — нет сложного сборочного pipeline, webpack, npm и т.д.
- **Быстрая первая загрузка** — HTML приходит готовым, нет клиентского рендеринга контента.
- **SEO-friendly** — поисковики видят полный HTML сразу.
- **Низкое потребление ресурсов в браузере** — почти нет JavaScript.
- **Кеширование HTML** — markdown рендерится один раз при сохранении.

### 9.2. Минусы подхода

- **Нет интерактивности** — комментарии, лайки, динамические фильтры без перезагрузки страницы требуют дополнительного JS.
- **KaTeX зависит от CDN** — если CDN недоступен, формулы не отобразятся.
- **Нет пагинации в поиске и тегах** — при большом количестве постов страница будет тяжёлой.
- **Нет темизации** — только один визуальный стиль.
- **Ограниченная DX** — нет hot-reload для CSS/JS отдельно от сервера (работает общий uvicorn reload).

---

## 10. Итог

Фронтенд `diegolonio.com` — это преднамеренно минималистичное серверное приложение. HTML строится шаблонами Jinja2, стили написаны на чистом CSS, а клиентский JavaScript сведён к одному редактору в админ-панели. Markdown превращается в HTML один раз при сохранении поста и кешируется в базе данных; математические формулы подготавливаются для рендеринга KaTeX, который выполняется уже в браузере.
