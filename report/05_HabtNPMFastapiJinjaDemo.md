# Отчёт по фронтенду: HabtNPMFastapiJinjaDemo

## Общая архитектура

Этот проект — учебное демо "FastAPI + Jinja2 + Tailwind", цель которого — показать чистую слоистую архитектуру бэкенда, не усложняя при этом фронтенд сборщиками (npm, webpack, vite).

**Используемые технологии и библиотеки:**
- **Jinja2 3.1.6:** Серверный рендеринг.
- **Tailwind CSS (CDN):** Стили.
- **Vanilla JS:** Один мини-скрипт (17 строк).

---

## Как связаны между собой элементы

### 1. Разделение шаблонов и наследование (Jinja2)
Файлы шаблонов логично разбиты:
- `base.html` (обертка)
- `partials/` (`navbar.html`, `footer.html`)
- `pages/` (`index.html`, `about.html`)

```jinja2
<!-- templates/base.html -->
<body class="h-full flex flex-col bg-slate-50 text-slate-800">
    {% include "partials/navbar.html" %}

    <main class="flex-1 max-w-3xl w-full mx-auto px-4 py-10">
        {% block content %}{% endblock %}
    </main>

    {% include "partials/footer.html" %}
    <script src="{{ url_for('static', path='js/main.js') }}"></script>
</body>
```
*Почему это сделано так:* Использование `{% include %}` позволяет выделить переиспользуемые блоки (шапку и подвал) в отдельные файлы, избавляя от дублирования кода. Класс `flex-1` у `main` и `flex-col` у `body` создают классический "Sticky Footer" (прижатый подвал).

### 2. Стилизация через Tailwind CDN
Tailwind подключается скриптом в `head`:
```html
<script src="https://cdn.tailwindcss.com"></script>
```
Классы прописываются прямо в разметке. Например, адаптивная сетка карточек на главной:
```html
<div class="grid gap-4 sm:grid-cols-3">
    {% for name, desc in features %}
    <div class="p-6 bg-white rounded-xl shadow-sm border border-slate-200">
        <h3 class="font-semibold text-slate-900">{{ name }}</h3>
        <p class="text-sm text-slate-500 mt-2">{{ desc }}</p>
    </div>
    {% endfor %}
</div>
```
*Почему это сделано так:* При загрузке страницы JS-скрипт сканирует DOM и генерирует CSS на лету. В демо-проекте это избавляет от необходимости поднимать Node.js окружение, писать `tailwind.config.js` и настраивать сборку CSS. `sm:grid-cols-3` показывает, что на мобильных будет одна колонка, а на экранах >640px — три колонки.

### 3. Интерактивность (main.js)
Единственная интерактивная часть — кнопка "Ping", которая стучится к API.
```javascript
// static/js/main.js
document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("ping-btn");
    const result = document.getElementById("ping-result");

    // Защита: скрипт подключен глобально,
    // но если кнопки на странице нет, он завершит работу.
    if (!button || !result) return;

    button.addEventListener("click", async () => {
        result.textContent = "Запрос...";
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
*Почему это сделано так:* Клиентский скрипт отделён от HTML, он перехватывает клик и отправляет AJAX запрос на эндпоинт того же домена, поэтому никаких проблем с CORS не возникает. Это классический пример гибридного подхода: основная страница рендерится сервером, а малая интерактивность "догружается" через JSON API.