"""Consultas SQL de la tabla users."""


def get_by_username(db, username: str):
    return db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = %s",
        (username,),
    ).fetchone()


def upsert(db, username: str, password_hash: str):
    """Crea el usuario, o actualiza su password si ya existe."""
    return db.execute(
        """
        INSERT INTO users (username, password_hash)
        VALUES (%s, %s)
        ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash
        RETURNING id
        """,
        (username, password_hash),
    ).fetchone()
