---

**Исходный код**: <a href="https://github.com/yashhere/fastapi-htmx-starter" target="_blank">https://github.com/yashhere/fastapi-htmx-starter</a>

---

# 🚀 Стартовый шаблон FastAPI + HTMX

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![HTMX](https://img.shields.io/badge/HTMX-Enabled-orange.svg)
![License](https://img.shields.io/badge/License-MIT-blue.svg)

*Современный production-ready стартовый шаблон для создания динамических веб-приложений на FastAPI, HTMX и TailwindCSS.*

[Возможности](#-возможности) • [Быстрый старт](#-быстрый-старт) • [Документация](#-документация) • [Участие в разработке](#-участие-в-разработке)

</div>

---

## 🌟 Почему этот шаблон?

Шаблон объединяет **скорость FastAPI** с **простотой HTMX** для создания современных веб-приложений без сложности тяжёлых JavaScript-фреймворков. В отличие от традиционного SPA-подхода, шаблон предлагает:

- **🎯 Никакой JavaScript-усталости** — создавайте динамические интерфейсы с помощью простых HTML-атрибутов
- **⚡ Максимальная производительность** — серверный рендеринг с минимальными накладными расходами на клиенте
- **🔧 Python повсюду** — отличный тип-безопасный код без необходимости писать TypeScript
- **📱 Прогрессивное улучшение** — работает без JavaScript, улучшается с ним
- **🎨 Современный UI/UX** — TailwindCSS для быстрого адаптивного дизайна
- **🔐 Готовая аутентификация** — полная система аутентификации из коробки

## ✨ Возможности

### 🎯 **Основные технологии**

- **[FastAPI](https://fastapi.tiangolo.com/)** — современный быстрый веб-фреймворк с автоматической документацией API
- **[HTMX](https://htmx.org/)** — мощные инструменты для HTML: создавайте динамические интерфейсы через атрибуты
- **[TailwindCSS](https://tailwindcss.com/)** — utility-first CSS-фреймворк для быстрой разработки UI
- **[SQLAlchemy 2.0](https://docs.sqlalchemy.org/)** — современная async ORM с полной поддержкой типов
- **[Alembic](https://alembic.sqlalchemy.org/)** — лёгкий инструмент для миграций базы данных

### 🔐 **Аутентификация и безопасность**

- Полная система управления пользователями на базе **[fastapi-users](https://fastapi-users.github.io/fastapi-users/)**
- Cookie-аутентификация с JWT-токенами (cookie `auth`, время жизни — 3600 секунд)
- Регистрация, вход, выход и управление профилем пользователя
- Защищённые маршруты и контроль доступа на основе активного пользователя
- Безопасное хеширование паролей по отраслевым стандартам

### 🎨 **Фронтенд**

- **Динамические взаимодействия** без написания JavaScript
- **Обновления в реальном времени** через частичную замену страниц HTMX
- **Адаптивный дизайн** с помощью утилит TailwindCSS
- **Состояния загрузки** и встроенная обработка ошибок
- **SEO-дружественный** серверный рендеринг

### 🛠️ **Опыт разработчика**

- **Современный Python** (3.12+) с полными аннотациями типов
- **Инструменты качества кода** — Black, Ruff, MyPy, Flake8, isort, djlint — преднастроены
- **Тестирование** через Pytest с поддержкой async
- **Миграции БД** через Alembic
- **CLI-команды** для типовых задач разработки
- **Hot-reload** dev-сервер

### 📦 **Готовность к production**

- **Конфигурация через окружение** с Pydantic Settings
- **Абстракция БД** — лёгкое переключение между SQLite, PostgreSQL и др.
- **Обработка ошибок** с кастомными exception handlers
- **Gzip-компрессия** ответов через middleware
- **Готовность к Docker** для деплоя

## 🚀 Быстрый старт

### Требования

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (рекомендуется) или pip для управления пакетами

### 1. 📁 Клонирование проекта

```bash
# Клонировать шаблон
git clone <your-template-repo-url> my-awesome-app
cd my-awesome-app

# Удалить git-историю, чтобы начать с чистого листа
rm -rf .git
git init
```

### 2. 🔧 Настройка окружения

```bash
# Создать и активировать виртуальное окружение через uv
uv venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Установить все зависимости
uv pip install -e .
```

### 3. ⚙️ Конфигурация

```bash
# Создать файл окружения
cp .env.example .env

# Сгенерировать безопасный секретный ключ и добавить в .env
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env

# Отредактировать .env под свои нужды
# DATABASE_URL, SECRET_KEY и т.д.
```

### 4. 🗄️ Настройка базы данных

```bash
# Создать начальную миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции для создания таблиц
alembic upgrade head
```

### 5. 🎉 Запуск приложения

```bash
# Запустить dev-сервер
uv run serve
# или
python -m app.cli serve

# Приложение доступно по адресу http://localhost:8000
```

**🎊 Готово! Ваше современное веб-приложение запущено!**

## 📁 Структура проекта

```
fastapi-htmx-starter/
├── 📁 app/
│   ├── 📁 api/              # Обработчики маршрутов
│   │   ├── auth.py          # Маршруты аутентификации
│   │   ├── items.py         # CRUD-пример (элементы)
│   │   ├── user.py          # Управление пользователем и профилем
│   │   └── dependencies.py  # Общие зависимости
│   ├── 📁 core/             # Основная логика приложения
│   │   ├── config.py        # Настройки (Pydantic Settings)
│   │   ├── database.py      # Подключение к БД и async-сессии
│   │   ├── templates.py     # Конфигурация Jinja2
│   │   └── users.py         # Логика аутентификации (fastapi-users)
│   ├── 📁 models/           # SQLAlchemy-модели
│   │   ├── user.py          # Модель пользователя
│   │   └── item.py          # Модель элемента (пример)
│   ├── 📁 schemas/          # Pydantic-схемы валидации
│   │   ├── user.py          # Схемы пользователя
│   │   └── item.py          # Схемы элемента
│   ├── 📁 services/         # Слой бизнес-логики
│   ├── 📁 static/           # Статические ресурсы (CSS, JS, изображения)
│   ├── 📁 templates/        # Jinja2 HTML-шаблоны
│   │   ├── base.jinja2      # Базовый шаблон
│   │   ├── index.jinja2     # Главная страница
│   │   ├── profile.jinja2   # Профиль пользователя
│   │   ├── 📁 auth/         # Шаблоны аутентификации (login, register)
│   │   ├── 📁 items/        # CRUD-шаблоны элементов
│   │   └── 📁 partials/     # HTMX partial-шаблоны
│   ├── 📁 tests/            # Тесты
│   ├── cli.py               # CLI-команды
│   └── main.py              # Точка входа FastAPI-приложения
├── 📁 alembic/              # Миграции базы данных
├── 📁 docs/                 # Подробная документация проекта
├── 📄 pyproject.toml        # Конфигурация проекта и зависимости
├── 📄 alembic.ini           # Конфигурация Alembic
├── 📄 .env.example          # Шаблон переменных окружения
├── 📄 AGENTS.md             # Правила для ИИ-ассистентов (агентов)
└── 📄 README.md             # Этот файл
```

## 🎯 Что включено

### 🔐 Полная система аутентификации

```python
# Регистрация пользователя с валидацией
POST /auth/register

# Вход/выход через cookie-сессии
POST /auth/cookie/login
POST /auth/cookie/logout

# Управление профилем
GET /users/me
PATCH /users/me
```

### 📝 CRUD-пример (элементы)

- ✅ Создание, чтение, обновление, удаление
- 🔍 Поиск и пагинация
- ✏️ Инлайн-редактирование через HTMX
- 🔄 Обновления в реальном времени без перезагрузки страницы

### 🎨 Современный фронтенд-стек

- **HTMX-взаимодействия**: динамические формы, живой поиск, частичные обновления
- **TailwindCSS-стили**: адаптивный mobile-first дизайн
- **Jinja2-шаблоны**: серверный рендеринг с наследованием шаблонов
- **Прогрессивное улучшение**: работает без JS, лучше — с ним

## 🛠️ Команды для разработки

```bash
# 🚀 Dev-сервер с hot-reload
uv run serve

# 🧪 Запуск тестов
uv run test

# 📝 Форматирование кода
uv run format

# 🔍 Линтинг кода
uv run lint

# 🔬 Проверка типов
uv run check-types
```

## 🗄️ Управление базой данных

```bash
# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "Add new feature"

# Применить ожидающие миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Посмотреть историю миграций
alembic history
```

## 🧪 Тестирование

Полноценная настройка тестирования с поддержкой async:

```bash
# Запустить все тесты с покрытием
pytest

# Запустить конкретный тест-файл
pytest app/tests/test_main.py -v

# Запустить тесты с детальным отчётом покрытия
pytest --cov=app --cov-report=html
```

## 🎨 Руководство по кастомизации

### 🔧 Добавление новых функций

1. **Создать новую модель**:

   ```python
   # app/models/post.py
   class Post(Base):
       __tablename__ = "posts"
       id: Mapped[int] = mapped_column(primary_key=True)
       title: Mapped[str] = mapped_column(String(100))
   ```

2. **Добавить API-маршруты**:

   ```python
   # app/api/posts.py
   @router.get("/posts")
   async def get_posts():
       # Ваша логика здесь
   ```

3. **Создать шаблоны**:

   ```html
   <!-- app/templates/posts/list.jinja2 -->
   <div hx-get="/posts" hx-trigger="load">
     <!-- Динамический контент -->
   </div>
   ```

### 🎨 Стили через TailwindCSS

```html
<!-- Красивые адаптивные компоненты -->
<button class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Нажми меня
</button>
```

### ⚡ Магия HTMX

```html
<!-- Живой поиск без JavaScript -->
<input hx-get="/search" hx-trigger="keyup changed delay:300ms"
       hx-target="#results" placeholder="Поиск...">
<div id="results"></div>
```

## 🚀 Деплой

### 🔧 Переменные окружения

**Обязательно для production:**

```bash
SECRET_KEY=your-super-secure-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
DEBUG=false
```

### 🐳 Деплой через Docker

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

# Установить uv и зависимости
RUN pip install uv && uv pip install --system -e .

# Применить миграции и запустить сервер
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### ☁️ Платформы для деплоя

Шаблон отлично работает с:

- **Railway** — деплой без конфигурации
- **Render** — автоматический деплой из git
- **Heroku** — классический PaaS
- **DigitalOcean App Platform** — управляемый деплой контейнеров
- **AWS / GCP / Azure** — полноценный облачный деплой

## 📚 Документация

Подробная документация о структуре и архитектуре проекта находится в папке [`docs/`](docs/):

| Файл | Описание |
|---|---|
| [`01_project_structure.md`](docs/01_project_structure.md) | Структура проекта и внешние зависимости |
| [`02_architecture.md`](docs/02_architecture.md) | Архитектура приложения |
| [`03_execution_flow.md`](docs/03_execution_flow.md) | Поток выполнения и таблица роутов |
| [`04_code_quality.md`](docs/04_code_quality.md) | Качество кода и инструменты |
| [`05_optimization_roadmap.md`](docs/05_optimization_roadmap.md) | План оптимизации |
| [`06_alembic.md`](docs/06_alembic.md) | Миграции БД: конфигурация, команды, рабочий процесс |
| [`07_frontend.md`](docs/07_frontend.md) | Фронтенд: шаблоны, HTMX-взаимодействия, стили, JS, проблемы и рекомендации |

> **Примечание для ИИ-ассистентов:** см. [`AGENTS.md`](AGENTS.md) — правила работы с кодовой базой.

## 🤝 Участие в разработке

Мы приветствуем вклад! Вот как вы можете помочь:

1. **🐛 Сообщать о багах** — откройте issue с подробностями
2. **💡 Предлагать фичи** — делитесь идеями
3. **📝 Улучшать документацию** — помогите другим разобраться
4. **🔧 Отправлять PR** — исправляйте баги или добавляйте функции

### Настройка для разработки

```bash
git clone <repo-url>
cd fastapi-htmx-starter
uv venv && source .venv/bin/activate
uv pip install -e .
pytest  # Убедитесь, что тесты проходят
```

## 📄 Лицензия

Проект распространяется под лицензией **MIT** — подробности в файле [LICENSE](LICENSE).

## 🙋‍♂️ Поддержка и сообщество

- **🐛 Issues**: [GitHub Issues](https://github.com/yashhere/fastapi-htmx-starter/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/yashhere/fastapi-htmx-starter/discussions)
- **📧 Email**: hello@yashagarwal.in

---

<div align="center">

**⭐ Если шаблон оказался полезен, поставьте звёздочку! ⭐**

Сделано с ❤️ [Yash Agarwal](https://yashagarwal.in)

</div>
