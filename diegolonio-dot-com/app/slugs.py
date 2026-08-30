"""Generación de slugs para las URLs de las entradas."""

import re
import unicodedata

from app.queries import posts


def make_slug(text: str) -> str:
    """'Descenso del gradiente' → 'descenso-del-gradiente'."""
    # Quita acentos: descompone 'é' en 'e' + tilde y descarta lo no-ASCII
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "post"


def unique_slug(db, text: str, exclude_id: int | None = None) -> str:
    """Slug único en la tabla posts; si ya existe agrega -2, -3, ...

    exclude_id: al editar, ignora el propio post (conservar su slug es válido).
    """
    base = make_slug(text)
    slug = base
    n = 2
    while posts.slug_exists(db, slug, exclude_id):
        slug = f"{base}-{n}"
        n += 1
    return slug
