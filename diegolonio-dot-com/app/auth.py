"""Autenticación: hash de passwords, cookie de sesión firmada y require_admin."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import settings

COOKIE_NAME = "session"

_hasher = PasswordHasher()
# Firma (no cifra) el contenido de la cookie: si alguien la modifica, la firma
# deja de ser válida. El timestamp permite expirarla con max_age.
_serializer = URLSafeTimedSerializer(settings.secret_key, salt="admin-session")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def create_session_token(username: str) -> str:
    return _serializer.dumps(username)


def get_session_username(request: Request) -> str | None:
    """Devuelve el username de la sesión, o None si no hay sesión válida."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        return _serializer.loads(token, max_age=settings.session_max_age)
    except (BadSignature, SignatureExpired):
        return None


def require_admin(request: Request) -> str:
    """Dependencia para rutas /admin: sin sesión válida, redirige al login."""
    username = get_session_username(request)
    if username is None:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})
    return username
