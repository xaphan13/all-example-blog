# Отчёт по фронтенду: fastAPIuser-suren

## Общая архитектура

Этот проект сфокусирован на бэкенд-функционале (подсистема управления пользователями), и его фронтенд-часть — это минимально жизнеспособные серверно-рендеренные HTML-страницы. Фронтенд не является полноценным приложением, а служит демонстрацией работы бэкенд-потоков (профиль, верификация).

**Используемые технологии и библиотеки:**
- **Jinja2:** Серверная шаблонизация.
- **Bootstrap 5.3.7 (CDN):** Стилизация интерфейса через классы.
- **Vanilla JS (fetch):** Обработка интерактивности.

---

## Как связаны между собой элементы

### 1. Шаблонизация (Jinja2)
Страницы наследуются от `templates/base.html`, который подключает Bootstrap:
```jinja2
<!-- templates/base.html -->
<head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.7/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <main class="container my-3">
        {% block main %}{% endblock %}
    </main>
</body>
```
*Почему это сделано так:* Bootstrap 5 предоставляет готовые классы (отступы, карточки, алерты), что позволяет разработчикам бэкенда быстро собирать UI без написания CSS.

### 2. Клиентские запросы через Fetch
Поскольку формы не отправляются классическим POST (из-за того, что бэкенд на fastapi-users ожидает JSON или специфичные данные), данные отправляются через `fetch` с использованием inline-скриптов.

Пример страницы верификации (`verification.html`):
```html
<script>
async function verifyEmail() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');

    try {
        const response = await fetch('/api/v1/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: token })
        });

        if (response.ok) {
            window.location.href = '/home/'; // Редирект при успехе
        }
    } catch (error) {
        // Показ Bootstrap Alert
        document.getElementById('error-message').classList.remove('d-none');
    }
}
verifyEmail();
</script>
```
*Почему это сделано так:* Бэкенд возвращает статус-коды и JSON-ответы, а не готовый HTML или редиректы. Использование `fetch` позволяет поймать ответ, проанализировать статус-код и изменить UI (скрыть спиннер, показать алерт или сделать редирект на JS).

### 3. Интеграция с Bootstrap (UI компоненты)
Проект использует утилитарные классы Bootstrap, но не подключает его JavaScript пакет. Это означает, что компоненты вроде модальных окон или dropdown не работают, но базовые элементы (кнопки, алерты, спиннеры) отрисовываются правильно:
```html
<!-- Использование Bootstrap классов -->
<div id="spinner" class="d-flex flex-column align-items-center">
    <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
    </div>
</div>
<div id="error-message" class="alert alert-danger d-none">
    An error occurred during verification.
</div>
```
*Почему это сделано так:* Это избавляет от необходимости писать кастомные стили (spinner, alert), а манипулирование видимостью (класс `d-none` — display: none) осуществляется простым JavaScript-кодом.

### 4. Особенности (и недочеты) архитектуры
- Проект не имеет страниц Login/Register. Предполагается, что авторизация тестируется через Swagger/Redoc.
- Весь JavaScript встроен (inline) в HTML.
- Шаблоны для отправки Email-сообщений реализованы без CSS стилей, на чистом HTML.