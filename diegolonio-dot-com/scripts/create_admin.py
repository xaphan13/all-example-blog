"""Crea (o actualiza el password de) el usuario administrador.

Uso: uv run python scripts/create_admin.py <username>
El password se pide por consola sin mostrarse en pantalla.
"""

import getpass
import sys
from pathlib import Path

import psycopg

# Permite importar app.* aunque el script viva en scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.auth import hash_password
from app.config import settings
from app.queries import users


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/create_admin.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirma el password: ")
    if not password:
        print("El password no puede estar vacío.")
        sys.exit(1)
    if password != confirm:
        print("Los passwords no coinciden.")
        sys.exit(1)

    with psycopg.connect(settings.database_url, row_factory=psycopg.rows.dict_row) as conn:
        users.upsert(conn, username, hash_password(password))

    print(f"Admin '{username}' listo.")


if __name__ == "__main__":
    main()
