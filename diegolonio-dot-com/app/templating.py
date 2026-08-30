"""Instancia compartida de Jinja2 para todos los routers."""

from time import time

from fastapi.templating import Jinja2Templates

from app.config import settings

templates = Jinja2Templates(directory="app/templates")

# Disponible en todas las plantillas sin pasarlo en cada ruta
templates.env.globals["base_url"] = settings.base_url

# Cache-busting: los CSS/JS propios se enlazan como /static/...?v={{ static_v }}.
# El valor cambia en cada arranque del servidor, así que tras un deploy (o un
# reload en dev) los navegadores descargan los archivos nuevos en vez de usar
# una copia vieja de su caché.
templates.env.globals["static_v"] = str(int(time()))


def _dateformat(value):
    """datetime → 'July 9, 2026' (formato de fecha del sitio, en inglés)."""
    if value is None:
        return ""
    return value.strftime("%B %-d, %Y")


templates.env.filters["dateformat"] = _dateformat
