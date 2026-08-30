"""Consultas SQL de la tabla posts."""

# Columnas completas de un post (sin search_vector, que es interno)
_COLUMNS = """
    id, slug, title, summary, cover_image, content_md, content_html,
    published, created_at, updated_at, published_at
"""


def list_published(db, limit: int, offset: int):
    """Entradas publicadas, de la más reciente a la más antigua (para el inicio)."""
    return db.execute(
        """
        SELECT id, slug, title, summary, cover_image, published_at
        FROM posts
        WHERE published
        ORDER BY published_at DESC
        LIMIT %s OFFSET %s
        """,
        (limit, offset),
    ).fetchall()


def count_published(db) -> int:
    return db.execute("SELECT count(*) AS n FROM posts WHERE published").fetchone()["n"]


def get_published_by_slug(db, slug: str):
    return db.execute(
        f"SELECT {_COLUMNS} FROM posts WHERE slug = %s AND published",
        (slug,),
    ).fetchone()


def get_prev(db, published_at):
    """Entrada publicada inmediatamente anterior (más antigua)."""
    return db.execute(
        """
        SELECT slug, title FROM posts
        WHERE published AND published_at < %s
        ORDER BY published_at DESC
        LIMIT 1
        """,
        (published_at,),
    ).fetchone()


def get_next(db, published_at):
    """Entrada publicada inmediatamente siguiente (más reciente)."""
    return db.execute(
        """
        SELECT slug, title FROM posts
        WHERE published AND published_at > %s
        ORDER BY published_at ASC
        LIMIT 1
        """,
        (published_at,),
    ).fetchone()


def list_all(db):
    """Todas las entradas (incluidos borradores), para el gestor del admin."""
    return db.execute(
        """
        SELECT id, slug, title, published, created_at, updated_at, published_at
        FROM posts
        ORDER BY created_at DESC
        """
    ).fetchall()


def get_by_id(db, post_id: int):
    return db.execute(
        f"SELECT {_COLUMNS} FROM posts WHERE id = %s",
        (post_id,),
    ).fetchone()


def create(db, slug, title, summary, cover_image, content_md, content_html, published):
    """Crea una entrada. published_at se fija solo si nace publicada."""
    return db.execute(
        """
        INSERT INTO posts
            (slug, title, summary, cover_image, content_md, content_html,
             published, published_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                CASE WHEN %s THEN now() END)
        RETURNING id
        """,
        (slug, title, summary, cover_image, content_md, content_html,
         published, published),
    ).fetchone()


def update(db, post_id, slug, title, summary, cover_image, content_md, content_html, published):
    """Actualiza una entrada. published_at se fija la primera vez que se publica."""
    return db.execute(
        """
        UPDATE posts SET
            slug = %s, title = %s, summary = %s, cover_image = %s,
            content_md = %s, content_html = %s, published = %s,
            published_at = CASE
                WHEN %s AND published_at IS NULL THEN now()
                ELSE published_at
            END,
            updated_at = now()
        WHERE id = %s
        RETURNING id
        """,
        (slug, title, summary, cover_image, content_md, content_html,
         published, published, post_id),
    ).fetchone()


def delete(db, post_id: int):
    db.execute("DELETE FROM posts WHERE id = %s", (post_id,))


def slug_exists(db, slug: str, exclude_id: int | None = None) -> bool:
    row = db.execute(
        "SELECT 1 FROM posts WHERE slug = %s AND id IS DISTINCT FROM %s",
        (slug, exclude_id),
    ).fetchone()
    return row is not None


def set_published(db, post_id: int, published: bool):
    """Publica o despublica. published_at se fija la primera vez que se publica."""
    db.execute(
        """
        UPDATE posts SET
            published = %s,
            published_at = CASE
                WHEN %s AND published_at IS NULL THEN now()
                ELSE published_at
            END,
            updated_at = now()
        WHERE id = %s
        """,
        (published, published, post_id),
    )


def list_published_by_tag(db, tag_slug: str):
    """Entradas publicadas con el tag dado (por slug), de la más reciente a la más antigua."""
    return db.execute(
        """
        SELECT p.id, p.slug, p.title, p.summary, p.cover_image, p.published_at
        FROM posts p
        JOIN post_tags pt ON pt.post_id = p.id
        JOIN tags t ON t.id = pt.tag_id
        WHERE p.published AND t.slug = %s
        ORDER BY p.published_at DESC
        """,
        (tag_slug,),
    ).fetchall()


def search(db, query: str, limit: int = 50):
    """Búsqueda full-text sobre search_vector, ordenada por relevancia.

    Usa websearch_to_tsquery (sintaxis tipo buscador: comillas, OR, -)
    con la misma config 'english' del tsvector generado. El LATERAL
    evita repetir la expresión del tsquery en WHERE y ORDER BY.
    """
    return db.execute(
        """
        SELECT p.id, p.slug, p.title, p.summary, p.cover_image, p.published_at
        FROM posts p
        CROSS JOIN LATERAL websearch_to_tsquery('english', %s) AS q
        WHERE p.published AND p.search_vector @@ q
        ORDER BY ts_rank(p.search_vector, q) DESC, p.published_at DESC
        LIMIT %s
        """,
        (query, limit),
    ).fetchall()


def list_texts(db):
    """Textos donde puede aparecer una imagen: contenido y portada de TODOS
    los posts (incluye borradores). Para detectar imágenes huérfanas en media/."""
    return db.execute("SELECT content_md, cover_image FROM posts").fetchall()
