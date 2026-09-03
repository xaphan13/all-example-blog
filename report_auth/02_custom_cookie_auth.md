# Часть 2: Кастомная авторизация с использованием подписанных Cookie

Иногда использование тяжеловесных библиотек для авторизации избыточно, и разработчики принимают решение написать свою систему аутентификации. В проекте **diegolonio-dot-com** реализован именно такой подход. Он базируется на двух основных столпах: надежное хеширование паролей и безопасное управление сессиями через подписанные Cookie.

## 1. Хеширование паролей (Argon2)

Для безопасного хранения паролей в базе данных проект использует алгоритм **Argon2**, который на сегодняшний день является одним из самых рекомендуемых стандартов. В коде (`diegolonio-dot-com/app/auth.py`) это реализовано с помощью библиотеки `argon2-cffi`:

```python
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return _hasher.hash(password)

def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False
```

Как видно из кода, создаются две простые функции-обертки: `hash_password` для создания хеша при регистрации/создании пользователя и `verify_password` для проверки введенного пароля при логине.

## 2. Управление сессиями (Подписанные Cookie)

Вместо хранения идентификаторов сессий в базе данных или использования JWT, проект использует механизм подписанных Cookie с помощью библиотеки `itsdangerous`. Суть подхода в том, что в Cookie сохраняется само имя пользователя (username), но оно криптографически подписывается секретным ключом сервера (`settings.secret_key`).

Если злоумышленник попытается изменить `username` в Cookie, подпись станет недействительной, и сервер отвергнет такую сессию.

```python
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from fastapi import Request
from app.config import settings

COOKIE_NAME = "session"

# Инициализация сериализатора с секретным ключом сервера
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="admin-session")

def create_session_token(username: str) -> str:
    """Создает токен (подписанную строку) для хранения в Cookie."""
    return _serializer.dumps(username)

def get_session_username(request: Request) -> str | None:
    """Извлекает и проверяет username из Cookie."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        # Проверяет подпись и срок действия (max_age)
        return _serializer.loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        return None
```

Функция `URLSafeTimedSerializer` также добавляет временную метку (timestamp) в токен, что позволяет задавать срок жизни сессии (`max_age`).

## 3. Защита маршрутов (Dependencies)

В FastAPI для защиты определенных URL-адресов (маршрутов) используется механизм зависимостей (Dependencies). В проекте создана зависимость `require_admin`, которая проверяет наличие валидной сессии:

```python
from fastapi import HTTPException, Request

def require_admin(request: Request) -> str:
    """
    Dependencia para rutas /admin: sin sesión válida, redirige al login.
    (Зависимость для маршрутов /admin: без валидной сессии перенаправляет на логин)
    """
    username = get_session_username(request)
    if username is None:
        # Если сессия недействительна, возвращаем 303 Redirect на страницу входа
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return username
```

Эта зависимость инжектируется в эндпоинты, которые требуют прав администратора (например, в `diegolonio-dot-com/app/routers/admin.py`), обеспечивая тем самым безопасность приватной части приложения.

## Итог

Такой подход (Argon2 + itsdangerous) отлично подходит для небольших проектов или админ-панелей. Он легковесен, не требует дополнительных обращений к базе данных для проверки сессии при каждом запросе (stateless) и обеспечивает высокий уровень безопасности при правильном хранении секретного ключа (`secret_key`).
