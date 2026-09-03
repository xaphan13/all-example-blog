# Часть 3: Авторизация с помощью fastapi-users

Для более сложных и масштабируемых проектов разработчики часто используют готовые библиотеки, предоставляющие комплексные решения "из коробки". В экосистеме FastAPI стандартом де-факто стала библиотека `fastapi-users`.

В нашем репозитории мы видим применение этой библиотеки в двух проектах: **fastAPIuser-suren** и **fastapi-htmx-starter**. Интересно, что несмотря на использование одного и того же инструмента, проекты выбрали разные стратегии работы с токенами.

## Общий концепт fastapi-users

Библиотека `fastapi-users` строится вокруг нескольких ключевых компонентов:
1.  **User Manager**: Управляет логикой работы с пользователями (создание, удаление, верификация).
2.  **Authentication Backend**: Связывает воедино способ передачи токена (Transport) и способ его валидации/хранения (Strategy).
3.  **Transport**: Как токен передается между клиентом и сервером (например, через Cookie или заголовок Bearer).
4.  **Strategy**: Как токен генерируется и проверяется (например, JWT или хранение в БД).

Оба рассматриваемых проекта используют **CookieTransport** — токен передается в HTTP-only Cookie, что является безопасным подходом для веб-приложений (защита от XSS).

## Проект 1: DatabaseStrategy (fastAPIuser-suren)

В проекте `fastAPIuser-suren` используется стратегия хранения токенов в базе данных (Database Strategy). Это означает, что при входе пользователя генерируется случайный токен, который сохраняется в таблице `access_tokens`. При каждом запросе сервер проверяет наличие этого токена в БД.

Вот как это настроено в `fastAPIuser-suren/fastapi-application/api/dependencies/authentication/strategy.py`:

```python
from fastapi_users.authentication.strategy.db import DatabaseStrategy

def get_database_strategy(
    access_tokens_db: Annotated[
        "AccessTokenDatabase[AccessToken]",
        Depends(get_access_tokens_db),
    ],
) -> DatabaseStrategy:
    return DatabaseStrategy(
        database=access_tokens_db, # Указание БД для работы с токенами
        lifetime_seconds=settings.access_token.lifetime_seconds,
    )
```

И сборка бэкенда аутентификации (`backend.py`):

```python
from fastapi_users.authentication import AuthenticationBackend
from core.authentication.transport import cookie_transport

authentication_backend = AuthenticationBackend(
    name="access-tokens-db",
    transport=cookie_transport, # Используем Cookie
    get_strategy=get_database_strategy, # Используем DB стратегию
)
```

**Плюсы подхода:** Вы можете легко отозвать (invalidte) любую сессию пользователя, просто удалив токен из БД.
**Минусы:** На каждый авторизованный запрос выполняется дополнительный запрос к базе данных для проверки токена.

## Проект 2: JWTStrategy (fastapi-htmx-starter)

Проект `fastapi-htmx-starter` использует совершенно иной подход — JSON Web Tokens (JWT). JWT — это криптографически подписанные токены, которые содержат всю необходимую информацию о пользователе внутри себя. Серверу не нужно обращаться к БД для их валидации.

Настройка в `fastapi-htmx-starter/app/core/users.py`:

```python
from fastapi_users.authentication import AuthenticationBackend, CookieTransport
from fastapi_users.authentication.strategy import JWTStrategy

# Настройка передачи токена через Cookie
cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600)

def get_jwt_strategy() -> JWTStrategy:
    # Инициализация JWT стратегии с секретным ключом
    return JWTStrategy(secret=settings.SECRET_KEY, lifetime_seconds=3600)

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
```

**Особенности интеграции с HTMX:**
Так как проект использует HTMX, процесс регистрации и входа тесно связан с рендерингом HTML. В `fastapi-htmx-starter/app/api/auth.py` мы видим, что успешная регистрация (даже через API) может возвращать разные ответы в зависимости от заголовков (например, редирект или HTML фрагмент).

```python
@router.get("/login", response_class=HTMLResponse)
async def get_login_page(
    request: Request,
    # Проверка текущего пользователя (опционально)
    user: User | None = Depends(fastapi_users.current_user(optional=True)),
):
    if user:
        # Если уже авторизован - редирект на главную
        return RedirectResponse(url=request.url_for("index"), status_code=302)
    return templates.TemplateResponse("auth/login.jinja2", {"request": request})
```

**Плюсы JWT:** Отсутствие нагрузки на базу данных (stateless).
**Минусы:** Сложно мгновенно отозвать токен до истечения срока его жизни.

## Итог
`fastapi-users` — это мощный инструмент, который позволяет гибко настраивать процесс авторизации, выбирая между Stateful (как в `fastAPIuser-suren`) и Stateless (как в `fastapi-htmx-starter`) архитектурой в зависимости от требований проекта.
