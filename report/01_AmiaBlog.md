# Отчёт по фронтенду: AmiaBlog

## Общая архитектура

Фронтенд проекта **AmiaBlog** реализует классический Server-Side Rendering (SSR) с небольшим слоем клиентского JavaScript. Бэкенд на FastAPI с помощью Jinja2 генерирует HTML, минифицирует его и отдаёт клиенту. Интерактивность достигается с использованием веб-компонентов Material Design (MDUI v2) и ванильного JavaScript.

**Используемые технологии и библиотеки:**
- **Jinja2:** Серверная шаблонизация.
- **MDUI v2.1.4:** UI-фреймворк на основе веб-компонентов (Material Design 3/You).
- **markdown-it 14.1.0:** Клиентский парсинг Markdown (с плагином сносок).
- **highlight.js 11.1.1:** Подсветка синтаксиса кода.
- **Vanilla JS & WebSockets:** Обработка взаимодействий, таких как Live Preview.

---

## Как связаны между собой элементы

### 1. Шаблонизация (Jinja2)
Все страницы наследуются от `templates/base.html`, который определяет общий каркас (`<head>`, навигацию, футер) и подключает глобальные статические файлы.
```jinja2
<!-- Подключение UI-фреймворка MDUI -->
<link rel="stylesheet" href="/static/mdui_2.1.4/mdui.css">
<script src="/static/mdui_2.1.4/mdui.global.js"></script>

<!-- Навигация: использование кастомных элементов MDUI -->
<mdui-navigation-drawer>
  <mdui-list>
    <mdui-list-item href="/">Home</mdui-list-item>
  </mdui-list>
</mdui-navigation-drawer>
```
*Почему это сделано так:* Наследование шаблонов позволяет переиспользовать общий каркас сайта (DRY) и применять изменения ко всем страницам разом.

### 2. Клиентский рендеринг Markdown
Контент постов хранится в базе в виде сырого Markdown. Вместо серверного рендеринга, браузер берет Markdown из скрытого блока и рендерит его на лету.
```html
<!-- Скрытый блок с Markdown -->
<pre style="display: none;" id="post-content">{{ post.content }}</pre>

<!-- Скрипт рендеринга (внутри шаблона post.html) -->
<script>
   function renderPage(){
     const md = window.markdownit({ html: true, linkify: true });
     // unescapeHtml восстанавливает экранированные сущности
     const result = md.render(unescapeHtml(mdui.$('#post-content')[0].innerHTML));
     mdui.$('#markdown-render-result')[0].innerHTML = result;
   }
   renderPage();
</script>
```
*Почему это сделано так:* Это переносит нагрузку по рендерингу Markdown на клиента и упрощает логику сервера (сервер хранит только Markdown и выдает его как есть). Также это позволяет легко внедрить функционал "Live Preview".

### 3. Подсветка синтаксиса
После рендеринга Markdown скрипт подключает нужные языковые бандлы highlight.js в зависимости от контента.
```jinja2
{% if hljs_languages %}
<script src="/static/hljs_11.1.1/highlight.min.js"></script>
{% for language in hljs_languages %}
<script src="/static/hljs_11.1.1/{{ language }}.min.js"></script>
{% endfor %}
<script>hljs.highlightAll();</script>
{% endif %}
```
*Почему это сделано так:* Загружаются только необходимые для конкретного поста языковые скрипты, что экономит трафик и ускоряет загрузку страницы.

### 4. Интерактивность без фреймворков
Дополнительная логика (поиск, сортировка постов) работает через базовые HTML-формы или простые JavaScript-обработчики:
```html
<mdui-select onchange="updateOrder(this.value)">...</mdui-select>

<script>
function updateOrder(order) {
    // обновление query-параметра в URL и перезагрузка страницы
    window.location.search = '?order=' + order;
}
</script>
```

### 5. Живое превью (Live Preview)
Связь клиента и сервера через WebSocket (`static/live_preview.js`):
1. Клиент подписывается на WebSocket `/api/live-preview-ws`.
2. При изменении файла на сервере присылается событие `update` с новым Markdown контентом.
3. Клиент перерендеривает блок Markdown без полной перезагрузки страницы.
```javascript
// Обработка сообщения от WebSocket
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'update') {
        mdui.$('#post-content')[0].innerHTML = escapeHtml(data.content);
        window._amiablog_renderPage();
    }
};
```
