# Отчёт по фронтенду: diegolonio-dot-com

## Общая архитектура

Проект **diegolonio-dot-com** построен по философии «без ORM, без CMS, без frontend-фреймворков». Весь HTML формируется на сервере (SSR) с использованием FastAPI и Jinja2, а клиентская часть предельно минималистична.

**Используемые технологии и библиотеки:**
- **Jinja2:** Серверная шаблонизация.
- **Vanilla CSS:** Написанные вручную стили (без препроцессоров вроде SASS или Tailwind).
- **Vanilla JS:** Один файл `editor.js` для функционала админки.
- **Внешние библиотеки (CDN):**
  - Font Awesome 6.5.1 (иконки)
  - KaTeX 0.16.9 (рендер математических формул)
  - Pygments (серверная подсветка кода, генерирующая CSS)

---

## Как связаны между собой элементы

### 1. Серверный рендеринг (Jinja2)
Все публичные страницы наследуют общий `base.html`, а админские — `admin/base_admin.html`.
```jinja2
<!-- app/templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <title>{% block title %}{% endblock %}</title>
    <!-- Cache busting через timestamp запуска сервера -->
    <link rel="stylesheet" href="/static/css/base.css?v={{ static_v }}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    <div class="{% block wrapper_class %}wrapper{% endblock %}">
        {% include "partials/header.html" %}
        <main>{% block content %}{% endblock %}</main>
        {% include "partials/footer.html" %}
    </div>
</body>
</html>
```
*Почему это сделано так:* Классический SSR подход обеспечивает высокую скорость первой отрисовки, отличную SEO-оптимизацию и не требует JavaScript для просмотра основного контента.

### 2. Рендеринг контента постов (Сервер + KaTeX)
Markdown преобразуется в HTML **один раз на сервере** при сохранении поста (используется `markdown-it-py`). Сгенерированный HTML сохраняется в PostgreSQL.
На клиент отправляется уже готовый HTML:
```jinja2
<article class="post-content">
    {{ post.content_html | safe }}
</article>
```

Однако формулы рендерятся уже в браузере при помощи KaTeX:
```html
<!-- Подключение скриптов KaTeX и рендеринг формул в DOM -->
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {
        delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
        ]
    });">
</script>
```
*Почему это сделано так:* Серверный рендер Markdown снижает нагрузку на клиент и улучшает SEO. KaTeX рендерит формулы на клиенте, так как серверу сложно генерировать правильный кросс-браузерный SVG/HTML для сложной математики.

### 3. Оформление стилей
Каждая логическая страница имеет свой CSS файл (например, `home.css`, `post.css`, `about.css`), которые подключаются поверх `base.css`.
Код подсвечивается классами, которые генерирует `Pygments` на сервере. Эти классы стилизуются через `pygments.css`:
```css
/* app/static/css/pygments.css */
.highlight .k { color: #008000; font-weight: bold } /* Ключевые слова */
.highlight .s { color: #BA2121 } /* Строки */
```

### 4. JavaScript в админке (`editor.js`)
Единственный клиентский скрипт обслуживает редактор постов в админ-панели, обеспечивая:
- Переключение вкладок "Edit" и "Preview"
- Загрузку изображений (Drag & Drop, Paste)
- Управление тегами (Chips)

```javascript
// Переключение превью (примерный код)
previewTab.addEventListener('click', async () => {
    // Отправка markdown на сервер
    const res = await fetch('/admin/api/preview', {
        method: 'POST',
        body: markdownContent
    });
    const html = await res.text();
    previewContainer.innerHTML = html;

    // Рендер формул в превью
    if (window.renderMathInElement) {
        renderMathInElement(previewContainer, {...});
    }
});
```
*Почему это сделано так:* Автор намеренно избегает сложных JS-фреймворков для максимального контроля и производительности. Ванильного JS более чем достаточно для функционала "написания статей".