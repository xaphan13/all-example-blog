# Отчёт по фронтенду: fastapi-htmx-starter

## Общая архитектура

Этот проект представляет собой Boilerplate, демонстрирующий мощную связку **FastAPI + HTMX + Tailwind CSS**. Вся интерактивность строится на концепции отправки HTML фрагментов с сервера вместо JSON (так называемый Hypermedia-Driven Application).

**Используемые технологии и библиотеки:**
- **Jinja2:** Серверная шаблонизация.
- **HTMX 2.0.4:** Запросы без написания JS и обновление фрагментов DOM.
- **Tailwind CSS (CDN):** Стилизация через утилитарные классы прямо в HTML-разметке.
- **Vanilla JS:** Около 150 строк встроенного (inline) скрипта для переключения модалок и глобальной обработки ошибок.

---

## Как связаны между собой элементы

### 1. Архитектура HTMX (Частичный свап)
Основа приложения — частичные обновления интерфейса (Partial Swaps) без полной перезагрузки страницы.

Например, для рендеринга списка "Items":
```jinja2
<!-- items/index.jinja2 -->
<div id="items-container">
    {% include "items/_table.jinja2" %}
</div>
```

Внутри таблицы каждая строка представляет собой Item. При клике "Edit", HTMX делает GET запрос к серверу:
```jinja2
<!-- items/_item_row.jinja2 -->
<tr id="item-{{ item.id }}">
    <td>{{ item.title }}</td>
    <td>
        <!-- При клике отправить GET на /items/{id}/edit и заменить весь <tr> -->
        <button hx-get="/items/{{ item.id }}/edit"
                hx-target="#item-{{ item.id }}"
                hx-swap="outerHTML">
            Edit
        </button>
    </td>
</tr>
```
Сервер отвечает шаблоном `_edit_form.jinja2`, который заменяет текущий `<tr>` на форму редактирования.
После редактирования форма делает `hx-put` запрос, и сервер возвращает обновлённый `_item_row.jinja2`, закрывая форму.

*Почему это сделано так:* Позволяет создавать Single Page Application (SPA)-подобный UX (inline-редактирование) вообще без использования React/Vue, оставляя всю логику и рендеринг на сервере.

### 2. Отправка данных в формате JSON (HTMX ext)
Бэкенд (FastAPI) спроектирован для приема JSON данных (через Pydantic модели). HTMX по умолчанию отправляет данные как `FormData`. Чтобы подружить их, используется расширение `json-enc`:
```html
<form hx-post="/items" hx-ext="json-enc" hx-target="#items-container">
    <input name="title" required>
    <button type="submit">Create</button>
</form>
```
*Почему это сделано так:* Бэкенду не нужно отдельно парсить `Form`-данные, он работает с привычными JSON Pydantic моделями, как в типичном REST API.

### 3. Стилизация (Tailwind CSS CDN)
Tailwind подключен через Play CDN прямо в `base.jinja2`:
```html
<script src="https://cdn.tailwindcss.com"></script>
```
Стиль описывается классами в HTML:
```html
<button class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
```
*Почему это сделано так:* Для стартового шаблона это ускоряет старт (не нужен Node.js и `npm install`). *Примечание: Для production рекомендуется настроить локальную сборку Tailwind.*

### 4. Встроенный JavaScript для управления ошибками
Глобальная обработка ошибок реализована в базовом шаблоне через прослушивание событий HTMX:
```javascript
document.body.addEventListener('htmx:responseError', function(evt) {
    const status = evt.detail.xhr.status;
    // Глобальное сообщение при ошибке 500
    if (status >= 500) {
        showGlobalMessage("Server error occurred", "red");
    }
});
```

Для локальных форм (например, авторизация), событие перехватывается и останавливается (`stopPropagation`), чтобы показать ошибку прямо в форме:
```html
<!-- auth/register.jinja2 -->
<script>
    document.getElementById('register-form').addEventListener('htmx:responseError', function(evt) {
        evt.stopPropagation(); // Не пускать к глобальному обработчику
        const response = JSON.parse(evt.detail.xhr.response);
        // Показать ошибку
    });
</script>
```
*Почему это сделано так:* HTMX отлично справляется с сетевыми запросами, но обработка кастомных JSON ошибок требует небольшого вмешательства на ванильном JS.