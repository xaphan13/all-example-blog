"""Runner de migraciones: aplica los .sql pendientes en orden numérico.

Uso: uv run python migrations/run_migrations.py

Lleva el registro de lo aplicado en la tabla schema_migrations, así que
correrlo varias veces es seguro (solo aplica lo que falta).
"""

import sys
from pathlib import Path

import psycopg

# Permite importar app.config aunque el script viva en migrations/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings

MIGRATIONS_DIR = Path(__file__).resolve().parent


def main():
    with psycopg.connect(settings.database_url) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   text        PRIMARY KEY,
                applied_at timestamptz NOT NULL DEFAULT now()
            )
            """
        )
        applied = {row[0] for row in conn.execute("SELECT filename FROM schema_migrations")}
        pending = [p for p in sorted(MIGRATIONS_DIR.glob("*.sql")) if p.name not in applied]

        if not pending:
            print("No hay migraciones pendientes.")
            return

        for path in pending:
            print(f"Aplicando {path.name} ...")
            conn.execute(path.read_text())
            conn.execute("INSERT INTO schema_migrations (filename) VALUES (%s)", (path.name,))

        print(f"Listo: {len(pending)} migración(es) aplicada(s).")


if __name__ == "__main__":
    main()
