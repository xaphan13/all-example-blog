"""Pool de conexiones psycopg 3 y dependencia get_db para FastAPI."""

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.config import settings

# open=False: el pool se abre en el lifespan de la app (main.py),
# no al importar el módulo. dict_row hace que cada fila sea un dict.
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)


def get_db():
    """Presta una conexión del pool durante la petición.

    Al salir del `with` la conexión hace COMMIT si todo salió bien
    (o ROLLBACK si hubo excepción) y regresa al pool.
    """
    with pool.connection() as conn:
        yield conn
