from pathlib import Path

# Base directories for project structure
_BASE_DIR = Path(__file__).parent.parent

# Static assets configuration
STATIC_DIR = _BASE_DIR / "app" / "static"
_ANSI_DIR = _BASE_DIR / "app" / "ansi"

# Directories for images
IMAGES_DIR = STATIC_DIR / "images"
HEADERS_DIR = IMAGES_DIR / "headers"

# Directories for ansi images
ANSI_IMAGES_DIR = _ANSI_DIR / "images"
ANSI_HEADERS_DIR = ANSI_IMAGES_DIR / "headers"
ANSI_THUMBNAILS_DIR = ANSI_IMAGES_DIR / "thumbnails"
