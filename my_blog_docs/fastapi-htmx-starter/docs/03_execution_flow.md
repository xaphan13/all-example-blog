# 03 — Логика и работа кода

## Жизненный цикл приложения

### Инициализация (startup)

```
uvicorn app.main:app --reload
  │
  ├─ 1. Импорт app/main.py
  │   ├─ app/core/config.py → settings = Settings() (загрузка .env)
  │   ├─ app/core/database.py → engine = create_async_engine(DATABASE_URL)
  │   │                        AsyncSessionLocal = async_sessionmaker(...)
  │   │                        Base = declarative_base()
  │   ├─ app/core/templates.py → templates = Jinja2Templates("app/templates")
  │   ├─ app/core/users.py → cookie_transport, JWTStrategy, auth_backend, fastapi_users
  │   ├─ app/models/user.py → User (модель загружается, метадата регистрируется в Base)
  │   └─ app/models/item.py → Item (модель загружается, метадата регистрируется в Base)
  │
  ├─ 2. Создание FastAPI-приложения
  │   app = FastAPI(title="FastAPI HTMX Starter", lifespan=lifespan)
  │   app.add_middleware(GZipMiddleware)
  │   app.mount("/static", StaticFiles(...))
  │
  ├─ 3. Регистрация роутеров
  │   ├─ fastapi_users.get_auth_router(auth_backend) → prefix="/auth/cookie"
  │   ├─ user_api_router.router → (без prefix, внутренний prefix="/users")
  │   ├─ auth_api_router.router → prefix="/auth"
  │   └─ items_api_router.router → prefix="/items"
  │
  ├─ 4. Регистрация exception handler
  │   app.exception_handler(HTTPException) → http_exception_handler
  │
  └─ 5. lifespan() — выполняется при старте ASGI-сервера
      ├─ Логирование: SECRET_KEY[:8], предупреждение о персистентности
      └─ await init_db() → Base.metadata.create_all (создание таблиц)
```

> **NB:** `init_db()` вызывает `Base.metadata.create_all`, что дублирует функцию Alembic-миграций. В CI-пайплайне (`ci.yml:57`) выполняется `alembic upgrade head`, но директория `alembic/versions/` пуста — миграций не существует.

### Завершение работы (shutdown)

`lifespan()` — после `yield` код отсутствует. Корректное закрытие `engine` не реализовано (нет `engine.dispose()`). ASGI-сервер закрывает соединения самостоятельно.

---

## Ключевые бизнес-процессы

### 1. Регистрация пользователя

```
POST /auth/register (HTMX, json-enc)
  │
  ├─ app/api/auth.py:38 → register_user()
  │   ├─ Валидация: UserCreate (Pydantic) → email, password
  │   ├─ user_manager.create(user_create, safe=True, request=request)
  │   │   ├─ Проверка уникальности email (SQLAlchemyUserDatabase)
  │   │   ├─ Валидация пароля (UserManager.validate_password)
  │   │   ├─ Хеширование (PasswordHelper.hash)
  │   │   ├─ INSERT в user-таблицу
  │   │   └─ on_after_register() → логирование
  │   ├─ HTMX → Response(200, HX-Redirect: /auth/login?registered=true)
  │   └─ Non-HTMX → RedirectResponse(302)
  │
  └─ При ошибке (email занят) → исключение пробрасывается → JSON error response
```

### 2. Вход (login)

```
POST /auth/cookie/login (HTMX form)
  │
  ├─ fastapi_users.get_auth_router(auth_backend) — встроенный роутер
  │   ├─ Валидация: OAuth2PasswordRequestForm (username=email, password)
  │   ├─ user_manager.authenticate() → проверка credentials
  │   ├─ auth_backend.login(strategy.write_token(user))
  │   │   ├─ JWTStrategy.write_token() → JWT-строка
  │   │   └─ CookieTransport.login() → Set-Cookie: auth=<jwt>; HttpOnly; SameSite=lax
  │   └─ Response: 204 No Content (успех) / 400 (ошибка)
  │
  └─ Клиентский JS (login.jinja2:52):
      xhr.status === 204 → window.location.href = '/'
      xhr.status === 400 → отображение ошибки в #auth-form-messages
```

### 3. CRUD Items (с HTMX-частичным обновлением)

#### List (поиск + пагинация)

```
GET /items?search=...&page=1&per_page=10
  │
  ├─ app/api/items.py:20 → list_items()
  │   ├─ SELECT Item WHERE owner_id = user.id [AND title ILIKE %search%]
  │   ├─ COUNT (через subquery) → total
  │   ├─ OFFSET/LIMIT → items
  │   ├─ Вычисление пагинации: total_pages, has_prev, has_next, page_range
  │   ├─ HTMX → TemplateResponse("items/_table.jinja2") — только таблица
  │   └─ Non-HTMX → TemplateResponse("items/index.jinja2") — полная страница
```

#### Create

```
POST /items (HTMX, json-enc: {title, description})
  │
  ├─ app/api/items.py:87 → create_item()
  │   ├─ Item(title, description, owner_id) → db.add → db.commit → db.refresh
  │   ├─ Повторный SELECT с пагинацией (page=1) — обновлённый список
  │   └─ TemplateResponse("items/_table.jinja2") — HTMX свопает таблицу
```

#### Edit → Update

```
GET /items/{id}/edit → app/api/items.py:165 → get_edit_item_form()
  └─ SELECT Item WHERE id AND owner_id → TemplateResponse("items/_edit_form.jinja2")
     (HTMX заменяет строку таблицы на форму редактирования)

PUT /items/{id} (HTMX, json-enc: {title, description})
  ├─ app/api/items.py:188 → update_item()
  │   ├─ SELECT Item WHERE id AND owner_id
  │   ├─ Обновление полей (если not None)
  │   ├─ db.commit → db.refresh
  │   └─ TemplateResponse("items/_item_row.jinja2") — HTMX заменяет форму на строку
```

#### Delete

```
DELETE /items/{id}?page=1&per_page=10&search=...
  ├─ app/api/items.py:234 → delete_item()
  │   ├─ SELECT Item WHERE id AND owner_id
  │   ├─ db.delete(item) → db.commit
  │   ├─ Повторный SELECT с пагинацией — обновлённый список
  │   └─ TemplateResponse("items/_table.jinja2")
```

#### Cancel edit

```
GET /items/{id}/cancel → app/api/items.py:313 → cancel_edit_item()
  └─ SELECT Item → TemplateResponse("items/_item_row.jinja2") — возврат в режим просмотра
```

### 4. Профиль пользователя

```
GET /profile → app/api/user.py:21 → get_profile_page()
  └─ SELECT User WITH selectinload(User.items) → TemplateResponse("profile.jinja2")

PATCH /profile/email (json-enc: {email: "..."})
  └─ app/api/user.py:42 → update_email()
      ├─ Проверка уникальности email
      ├─ user.email = new_email → db.commit
      └─ HTMLResponse (inline HTML — f-string, без шаблона)

PATCH /profile/password (json-enc: {current_password, password, confirm_password})
  └─ app/api/user.py:89 → update_password()
      ├─ Проверка совпадения password == confirm_password
      ├─ PasswordHelper.verify_and_update(current_password, hashed_password)
      ├─ UserManager.validate_password(new_password)
      ├─ PasswordHelper.hash(new_password) → user.hashed_password → db.commit
      └─ HTMLResponse (inline HTML — f-string)
```

---

## Роутинг и middleware

### Middleware

| Middleware | Файл | Назначение |
|---|---|---|
| `GZipMiddleware` | `app/main.py:43` | Gzip-компрессия ответов |

> CORS middleware отсутствует, несмотря на закомментированный `CORS_ORIGINS` в `.env.example`.

### Таблица роутов

| Метод | Путь | Хендлер | Источник | Auth |
|---|---|---|---|---|
| `GET` | `/` | `index` | `app/main.py:108` | Optional |
| `GET` | `/auth/login` | `get_login_page` | `app/api/auth.py:16` | Optional (redirect if logged in) |
| `GET` | `/auth/register` | `get_register_page` | `app/api/auth.py:27` | Optional (redirect if logged in) |
| `POST` | `/auth/register` | `register_user` | `app/api/auth.py:38` | Public |
| `POST` | `/auth/logout` | `logout_user` | `app/api/auth.py:71` | Required |
| `POST` | `/auth/cookie/login` | fastapi-users built-in | `app/main.py:52` | Public |
| `POST` | `/auth/cookie/logout` | fastapi-users built-in | `app/main.py:52` | Required |
| `GET` | `/users/me` | fastapi-users built-in | `app/api/user.py:178` | Required |
| `PATCH` | `/users/me` | fastapi-users built-in | `app/api/user.py:178` | Required |
| `GET` | `/profile` | `get_profile_page` | `app/api/user.py:21` | Required (active) |
| `PATCH` | `/profile/email` | `update_email` | `app/api/user.py:42` | Required (active) |
| `PATCH` | `/profile/password` | `update_password` | `app/api/user.py:89` | Required (active) |
| `GET` | `/items` | `list_items` | `app/api/items.py:20` | Required (active) |
| `POST` | `/items` | `create_item` | `app/api/items.py:87` | Required (active) |
| `GET` | `/items/{id}/edit` | `get_edit_item_form` | `app/api/items.py:165` | Required (active) |
| `PUT` | `/items/{id}` | `update_item` | `app/api/items.py:188` | Required (active) |
| `DELETE` | `/items/{id}` | `delete_item` | `app/api/items.py:234` | Required (active) |
| `GET` | `/items/{id}/cancel` | `cancel_edit_item` | `app/api/items.py:313` | Required (active) |
| `GET` | `/static/*` | `StaticFiles` | `app/main.py:49` | Public |

---

## Обработка ошибок

### Серверная сторона

`app/main.py:71` — `http_exception_handler`:

| Status | HTMX-запрос | Non-HTMX |
|---|---|---|
| `401` | `Response(200, HX-Redirect: /auth/login)` | `RedirectResponse(302 → /auth/login)` |
| Другие | `JSONResponse(status, {"detail": ...})` | `JSONResponse(status, {"detail": ...})` |

> **NB:** Обработчик перехватывает только `HTTPException`. Необработанные исключения (500) попадают в дефолтный FastAPI handler.

### Клиентская сторона (JS в `base.jinja2`)

- `htmx:responseError` (строки 105-126): для 5xx — глобальное сообщение об ошибке; для 4xx — только если target не в `#register-form` / `#login-form`
- `htmx:sendError` (строки 128-135): глобальное сообщение о сетевой ошибке
- `login.jinja2:52`: перехват `htmx:afterRequest` — при 204 редирект на `/`, при 400 — inline-ошибка
- `register.jinja2:48`: перехват `htmx:responseError` — парсинг JSON-ошибки, inline-сообщение

---

## Логирование

| Компонент | Уровень | Метод |
|---|---|---|
| Root | `INFO` | `logging.basicConfig(level=logging.INFO)` в `app/main.py:23` |
| `app.main` | `INFO` | Startup-сообщения, SECRET_KEY prefix |
| `app.api.auth` | `INFO`/`ERROR` | Регистрация, logout, ошибки регистрации |
| `app.models.user` | `INFO` | `on_after_register`, `on_after_forgot_password`, `on_after_request_verify` |

> **NB:** Структурированное логирование отсутствует. Логи пишутся в `stderr` через `basicConfig`. Нет rotation, нет JSON-формата, нет correlation IDs.
