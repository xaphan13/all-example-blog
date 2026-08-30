"""Limpieza de imágenes huérfanas en media/.

Subir una imagen y guardar el post son operaciones independientes: si una
imagen se sube desde el editor pero luego se borra del texto (o el post
nunca se guarda), el archivo queda huérfano en media/. Aquí se comparan
los archivos del disco contra las URLs /media/... que aparecen en los
posts y se borra lo que nadie referencia.
"""

from pathlib import Path
from time import time

from app.config import settings
from app.queries import posts

# No se tocan archivos subidos hace poco: pueden estar referenciados solo
# en el textarea de un editor abierto cuyo post aún no se ha guardado.
MIN_AGE_SECONDS = 60 * 60  # 1 hora


def delete_orphans(db) -> list[str]:
    """Borra las imágenes de media/ que ningún post referencia.

    Devuelve las URLs borradas. También elimina las subcarpetas que
    queden vacías (p. ej. media/<slug>/ de un post migrado y borrado).
    """
    media_dir = Path(settings.media_dir)

    # Todo el texto donde puede vivir una URL de imagen, en un solo blob.
    # Los nombres son UUIDs (o van bajo media/<slug>/), así que buscar la
    # URL completa como subcadena no da falsos positivos.
    blob = "\n".join(
        f"{row['content_md']}\n{row['cover_image'] or ''}"
        for row in posts.list_texts(db)
    )

    deleted = []
    now = time()
    for path in media_dir.rglob("*"):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        if now - path.stat().st_mtime < MIN_AGE_SECONDS:
            continue
        url = f"/media/{path.relative_to(media_dir).as_posix()}"
        if url not in blob:
            path.unlink()
            deleted.append(url)

    # De adentro hacia afuera, por si hay carpetas anidadas vacías
    for folder in sorted((p for p in media_dir.rglob("*") if p.is_dir()), reverse=True):
        if not any(folder.iterdir()):
            folder.rmdir()

    return deleted
