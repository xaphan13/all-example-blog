# Tailwind CSS: CDN vs Production-сборка

> **Контекст.** В демо-проекте Tailwind подключается через CDN-скрипт прямо в `base.html`.
> Это сознательный компромисс: проект демонстрирует архитектуру бэкенда (FastAPI + Jinja2),
> а не настройку фронтенд-сборки. В продакшене подход полностью меняется.

---

## 1. Что такое «Tailwind через CDN»

В `templates/base.html` используется такая строка:

```html
<script src="https://cdn.tailwindcss.com"></script>
```

Этот скрипт — полноценный компилятор Tailwind, работающий **в браузере посетителя**:

1. **Скачивается** с CDN (~100 КБ сжатого JavaScript).
2. **Парсит весь HTML-документ**, собирая все CSS-классы, с которыми встречает.
3. **Генерирует CSS** на основе найденных классов, подставляя его в `<style>` прямо на странице.
4. **Добавляет поддержку** `tailwind.config.js` через мета-тег `<script id="tailwind-config">`.

### Что это даёт в демо

| Преимущество | Описание |
|---|---|
| **Нулевая настройка** | Не нужен `package.json`, `npm install`, PostCSS. |
| **Мгновенный старт** | `pip install -r requirements.txt && uvicorn main:app` — и всё работает. |
| **Нет артефактов сборки** | Не нужно генерировать `.css` файлы, не нужно их кэшировать. |
| **Гибкая конфигурация** | Можно менять цвета и конфиг прямо в шаблоне через мета-тег. |
| **Идеально для статей** | Читатель не видит шагов с `npm` — фокус на бэкенде. |

---

## 2. Почему CDN-подход плох для продакшена

### 2.1 Производительность и размер

| Метрика | CDN | Production-сборка |
|---|---|---|
| Размер CSS | ~3 МБ (все классы) | 10–50 КБ (только используемые) |
| Доп. JS-запрос | Да, ~100 КБ | Нет |
| Генерация CSS | На клиенте (CPU) | На сервере при сборке (ноль затрат) |
| Повторная генерация | Каждая страница, каждый клиент | Один раз при деплое |

**Пояснение.** CDN-скрипт генерирует CSS со **всеми** 8000+ утилитарными классами Tailwind, даже если в проекте используются 200. Браузер должен загрузить ~3 МБ CSS, а затем ещё 100 КБ JS, чтобы собрать из них итоговый стиль. В продакшене `--minify` удаляет всё неиспользуемое и выдаёт файл на 50–300 раз меньше.

### 2.2 Время до отрисовки (FCP / LCP)

Процесс отрисовки при CDN-подключении выглядит так:

```
Запрос страницы → Браузер парсит HTML → Находит <script src="cdn">
→ Скачивает скрипт (~100 КБ) → Парсит весь HTML, ищет классы
→ Генерирует CSS → Вставляет <style> → Только потом рисует контент
```

На медленных устройствах (телефоны, планшеты) этот процесс занимает **500–2000 мс** только на генерацию CSS. Статический CSS-файл браузер просто загружает и применяет — никаких вычислений.

### 2.3 Content Security Policy (CSP)

Если сайт использует CSP (что рекомендуется для безопасности):

```
Content-Security-Policy: script-src 'self'
```

CDN-скрипт **не выполнится** — он заблокируется. Придётся либо:

- Расширять CSP: `script-src 'self' https://cdn.tailwindcss.com 'unsafe-inline'`
- Либо полностью отказаться от CDN.

Расширение CSP ослабляет защиту от XSS-атак. Production-сборка не требует дополнительных `script-src` правил.

### 2.4 Кэширование

| Метрика | CDN | Production-сборка |
|---|---|---|
| Кэширование CSS | Нельзя (генерируется динамически) | Можно навсегда (`max-age=31536000`) |
| Кэширование JS-скрипта | Да, но бессмысленно (генерация всё равно каждая страница) | Н/А |
| HTTP-запросов | 1 скрипт + 1 CSS (генерируемый) | 1 статический CSS (кэшируется) |

Статический CSS-файл можно закэшировать браузером **навсегда**. При каждом обновлении страницы браузер не скачивает его повторно. С CDN-скриптом браузер каждый раз скачивает JS и пересчитывает CSS заново.

### 2.5 Надёжность и офлайн

- CDN может быть недоступен (блокировка, проблемы с провайдером, геоблокировка).
- Без CDN сайт **не отобразится** — все стили пропадут.
- Статический CSS — часть вашего репозитория, ваш контроль.

### 2.6 SEO и Core Web Vitals

Google учитывает Core Web Vitals при ранжировании:

- **FCP** (First Contentful Paint) — страдает из-за задержки генерации CSS.
- **LCP** (Largest Contentful Paint) — страдает по той же причине.
- **CLS** (Cumulative Layout Shift) — может страдать, если стили подгружаются с задержкой.

Production-сборка даёт стабильные, предсказуемые метрики.

---

## 3. Production-сборка Tailwind: пошаговое руководство

### Шаг 1: Установка зависимостей

```bash
cd /путь/к/проекту
npm install -D tailwindcss postcss autoprefixer
```

**Что устанавливается:**

| Пакет | Зачем нужен |
|---|---|
| `tailwindcss` | Сам фреймворк + CLI-инструмент для сборки |
| `postcss` | Постпроцессор CSS, на котором работает Tailwind |
| `autoprefixer` | Добавляет вендорные префиксы (`-webkit-`, `-moz-`) |

**Результат:** в `package.json` появится секция `devDependencies`, в корне — папка `node_modules`.

### Шаг 2: Инициализация конфигурации

```bash
npx tailwindcss init -p
```

**Что создаётся:**

| Файл | Назначение |
|---|---|
| `tailwind.config.js` | Конфигурация: какие файлы сканировать, кастомные темы, плагины |
| `postcss.config.js` | Настройка PostCSS-плагина для Tailwind |

**Пример `tailwind.config.js`:**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  // Какие файлы сканировать на наличие классов Tailwind
  content: [
    "./templates/**/*.html",   // все HTML-шаблоны Jinja
    "./static/**/*.js",        // JS-файлы, если используются классы динамически
  ],
  // Кастомизация темы (опционально)
  theme: {
    extend: {
      colors: {
        primary: "#1a1a2e",
        accent: "#e94560",
      },
    },
  },
  // Плагины (опционально)
  plugins: [],
};
```

**Ключевой параметр `content`.** Tailwind сканирует эти файлы и запоминает все использованные классы. При сборке **остаются только они**. Если класс есть в HTML, но не указан в `content` — он будет удалён.

### Шаг 3: Создание базового CSS-файла

Создаём файл `static/css/tailwind.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Что означают директивы:**

| Директива | Что делает |
|---|---|
| `@tailwind base` | Сброс стилей (preflight) — нормализует базовые элементы (заголовки, параграфы, кнопки) |
| `@tailwind components` | Компоненты-базы (формы, таблицы, навигация) — расширяемые базовые стили |
| `@tailwind utilities` | Утилитарные классы (`mt-4`, `flex`, `text-red-500` и т.д.) — основная магия Tailwind |

### Шаг 4: Сборка CSS

#### Для разработки (watch-режим)

```bash
npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --watch
```

| Флаг | Значение |
|---|---|
| `-i` | Входной файл (источник с `@tailwind`-директивами) |
| `-o` | Выходной файл (сгенерированный CSS) |
| `--watch` | Следить за изменениями и пересобирать автоматически |

#### Для продакшена (минификация + очистка)

```bash
npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify
```

| Флаг | Значение |
|---|---|
| `--minify` | Удаляет все неиспользуемые классы + минифицирует CSS |

**Результат.** Файл `static/css/output.css` содержит **только те классы, которые найдены** в файлах из `content`. Если в проекте 200 классов вместо 8000 — файл будет в 40 раз меньше.

### Шаг 5: Обновление шаблона

**Удаляем из `templates/base.html`:**

```html
<!-- ❌ УДАЛИТЬ -->
<script src="https://cdn.tailwindcss.com"></script>
```

**Добавляем:**

```html
<!-- ✅ ЗАМЕНИТЬ НА -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/output.css') }}">
```

### Шаг 6: Настройка статических файлов (FastAPI)

Убедитесь, что FastAPI раздаёт `static/` корректно (обычно уже настроено в `main.py`):

```python
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Шаг 7: Автоматизация сборки в CI/CD

#### Вариант A: GitHub Actions

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: npm ci

      - name: Build Tailwind CSS
        run: npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Deploy
        run: |
          gunicorn main:app --workers 4 --bind 0.0.0.0:8000
```

#### Вариант B: `package.json` + локальная сборка

```json
{
  "name": "habt-npm-fastapi-jinja-demo",
  "private": true,
  "scripts": {
    "build:css": "npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify",
    "build": "npm run build:css",
    "dev:css": "npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --watch"
  },
  "devDependencies": {
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0"
  }
}
```

Сборка однимcmd: `npm run build`

### Шаг 8: Docker — сборка CSS внутри образа

**Dockerfile:**

```dockerfile
FROM python:3.12-slim AS backend

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# --- Этап сборки CSS ---
FROM node:20-alpine AS css-builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify

# --- Финальный образ ---
FROM python:3.12-slim

WORKDIR /app
COPY --from=css-builder /app/static /app/static
COPY --from=backend /app /app

EXPOSE 8000
CMD ["gunicorn", "main:app", "--workers", "4", "--bind", "0.0.0.0:8000"]
```

**compose.yaml:**

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
```

Сборка: `docker compose up --build`

CSS собирается один раз на этапе билда образа и попадает в финальный контейнер.

---

## 4. Расширенная конфигурация для продакшена

### 4.1 PurgeCSS (встроен в Tailwind v3+)

В Tailwind v3+ PurgeCSS встроен по умолчанию. Флаг `--minify` включает его автоматически.

### 4.2 Source Maps (для отладки)

```bash
npx tailwindcss -i ./static/css/tailwind.css -o ./static/css/output.css --minify --source-map
```

Создаёт `output.css.map` — позволяет отлаживать в DevTools, какой HTML-элемент использует какой класс.

### 4.3 JIT-режим (Just-In-Time)

Tailwind v3 работает в JIT-режиме по умолчанию. Это значит:

- Классы генерируются **на лету** при сканировании файлов.
- Не нужно «предустанавливать» классы.
- Поддержка **произвольных значений**: `bg-[#1a1a2e]`, `w-[300px]`.
- Поддержка **арbitrary modifiers**: `bg-red-500/50` (50% прозрачности).

### 4.4 Плагин forms

Если в проекте есть формы:

```bash
npm install -D @tailwindcss/forms
```

```javascript
// tailwind.config.js
module.exports = {
  content: ["./templates/**/*.html"],
  plugins: [
    require("@tailwindcss/forms"),
  ],
};
```

### 4.5 Плагин typography

Для красивого markdown/контента:

```bash
npm install -D @tailwindcss/typography
```

```javascript
// tailwind.config.js
module.exports = {
  content: ["./templates/**/*.html"],
  plugins: [
    require("@tailwindcss/typography"),
  ],
};
```

Использование: `<div class="prose">...</div>`

### 4.6 Оптимизация размера

Если файл всё ещё большой:

1. **Проверьте `content`** — не указаны ли лишние пути (например, `./**/*.html` рекурсивно во всех папках).
2. **Убедитесь**, что в `content` нет `node_modules`.
3. **Используйте `--minify`** — он обязательно удаляет неиспользуемые классы.
4. **Проверьте DevTools** — Network → CSS → посмотрите размер `output.css`.

---

## 5. Сравнительная таблица

| Критерий | CDN | Production-сборка |
|---|---|---|
| **Сложность настройки** | 0 шагов | 5–8 шагов |
| **Начальные зависимости** | Нет | `npm install` |
| **Размер CSS** | ~3 МБ (все классы) | 10–50 КБ (очищенный) |
| **Доп. JS-запрос** | ~100 КБ | 0 |
| **Генерация CSS** | На клиенте (каждый раз) | На сервере (один раз) |
| **Кэширование** | Нельзя | Можно навсегда |
| **CSP-совместимость** | ❌ Требует расширения | ✅ Работает с любым |
| **Офлайн-режим** | ❌ Не работает | ✅ Работает |
| **FCP / LCP** | Страдают | Оптимальные |
| **CLS** | Может страдать | Стабильный |
| **CI/CD** | Не нужен | Нужен шаг сборки |
| **Docker** | Проще | Мультистейдж-сборка |
| **Гибкость конфига** | Через мета-тег в HTML | Через `tailwind.config.js` |

---

## 6. Итоги

### Когда CDN-подход уместен

- 📝 Статьи и документация
- 🎓 Демо и прототипы
- 🧪 Быстрые MVP
- 📊 Внутренние инструменты

### Когда production-сборка обязательна

- 🌐 Публичные сайты
- 📱 Мобильный трафик
- 🔒 Требования CSP
- 📈 SEO-ориентированные проекты
- 🏢 Корпоративные продукты

### Разница в цифрах

```
CDN:     3 000 000 байт CSS  +  100 000 байт JS  =  3 100 000 байт
Prod:         20 000 байт CSS  +            0 байт  =     20 000 байт

Экономия:  155 раз по объёму данных
```

### Рекомендация для данного проекта

Текущий CDN-подключение — **осознанный выбор для демо**. При переходе в продакшен следует:

1. Добавить `package.json` и зависимости Tailwind.
2. Создать `tailwind.config.js` с правильным `content`.
3. Создать `static/css/tailwind.css` с директивами `@tailwind`.
4. Настроить сборку `--minify` (вручную или в CI/CD).
5. Заменить `<script>` в `base.html` на `<link rel="stylesheet">`.
6. Настроить Dockerfile с мультистейдж-сборкой CSS (опционально).

Это займёт 10–15 минут и даст **кратный прирост производительности** для каждого пользователя.

---

*Создано на основе анализа проекта HabtNPMFastapiJinjaDemo.*
