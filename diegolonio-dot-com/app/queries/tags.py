"""Consultas SQL de tags y su relación con posts (post_tags)."""


def get_by_slug(db, slug: str):
    return db.execute(
        "SELECT id, name, slug FROM tags WHERE slug = %s",
        (slug,),
    ).fetchone()


def get_or_create(db, name: str, slug: str):
    """Devuelve el tag si existe (por slug); si no, lo crea."""
    existing = get_by_slug(db, slug)
    if existing:
        return existing
    return db.execute(
        "INSERT INTO tags (name, slug) VALUES (%s, %s) RETURNING id, name, slug",
        (name, slug),
    ).fetchone()


def list_for_post(db, post_id: int):
    return db.execute(
        """
        SELECT t.id, t.name, t.slug
        FROM tags t
        JOIN post_tags pt ON pt.tag_id = t.id
        WHERE pt.post_id = %s
        ORDER BY t.name
        """,
        (post_id,),
    ).fetchall()


def set_for_post(db, post_id: int, tag_ids: list[int]):
    """Reemplaza los tags de un post por la lista dada."""
    db.execute("DELETE FROM post_tags WHERE post_id = %s", (post_id,))
    for tag_id in tag_ids:
        db.execute(
            "INSERT INTO post_tags (post_id, tag_id) VALUES (%s, %s)",
            (post_id, tag_id),
        )
