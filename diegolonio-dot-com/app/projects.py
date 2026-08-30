"""Carga de los proyectos destacados desde projects.yaml (raíz del repo)."""

from pathlib import Path

import yaml

# Ruta al yaml en la raíz del repo (dos niveles arriba de este archivo)
PROJECTS_FILE = Path(__file__).resolve().parent.parent / "projects.yaml"


def load_projects() -> list[dict]:
    """Lee projects.yaml y devuelve la lista de proyectos.

    Cada proyecto es un dict con las claves name, description, url e icon.
    Si el archivo no existe (o está vacío), devuelve una lista vacía.
    """
    if not PROJECTS_FILE.exists():
        return []

    with PROJECTS_FILE.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or []
