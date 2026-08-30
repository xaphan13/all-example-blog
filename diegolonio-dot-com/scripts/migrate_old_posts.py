"""Migra los posts del sitio viejo (Go) a la BD y media/ del sitio nuevo.

Uso: uv run python scripts/migrate_old_posts.py

Formato de los .md viejos: línea 1 = título, línea 2 = fecha (YYYY-MM-DD),
línea 3 = resumen, línea 4 = imagen de portada, resto = cuerpo markdown.

Es idempotente: si el slug ya existe, actualiza la entrada en vez de duplicarla.
Las imágenes se copian a media/<slug>/ y las rutas /static/img/<slug>/ del
markdown se reescriben a /media/<slug>/.
"""

import shutil
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings
from app.markdown_render import render_markdown
from app.queries import posts

OLD_SITE = Path.home() / "Documents" / "wwwdiegolonio"


def migrate_post(conn, md_file: Path):
    slug = md_file.stem
    lines = md_file.read_text().splitlines()
    title, date, summary, cover = (line.strip() for line in lines[:4])
    body = "\n".join(lines[4:]).strip()

    # Copia las imágenes del post a media/<slug>/ y reescribe sus rutas
    old_img_dir = OLD_SITE / "static" / "img" / slug
    if old_img_dir.is_dir():
        new_img_dir = Path(settings.media_dir) / slug
        new_img_dir.mkdir(parents=True, exist_ok=True)
        for img in old_img_dir.iterdir():
            shutil.copy2(img, new_img_dir / img.name)
            print(f"  imagen: {img.name}")
    body = body.replace(f"/static/img/{slug}/", f"/media/{slug}/")
    cover = cover.replace(f"/static/img/{slug}/", f"/media/{slug}/")

    content_html = render_markdown(body)

    existing = conn.execute("SELECT id FROM posts WHERE slug = %s", (slug,)).fetchone()
    if existing:
        posts.update(conn, existing["id"], slug, title, summary, cover,
                     body, content_html, True)
        post_id = existing["id"]
        action = "actualizado"
    else:
        post_id = posts.create(conn, slug, title, summary, cover,
                               body, content_html, True)["id"]
        action = "creado"

    # Conserva la fecha de publicación original del sitio viejo
    conn.execute(
        "UPDATE posts SET published_at = %s, created_at = %s WHERE id = %s",
        (date, date, post_id),
    )
    print(f"  {action}: '{title}' ({date})")


def main():
    md_files = sorted((OLD_SITE / "posts").glob("*.md"))
    if not md_files:
        print(f"No hay posts en {OLD_SITE / 'posts'}")
        return

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn:
        for md_file in md_files:
            print(f"Migrando {md_file.name} ...")
            migrate_post(conn, md_file)

    print("Listo.")


if __name__ == "__main__":
    main()
