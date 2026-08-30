from pathlib import Path

# Base directories for project structure
_BASE_DIR = Path(__file__).parent.parent
_CONTENT_DIR = _BASE_DIR / "content"

# Content organization (used to render dynamic pages)
AUTHOR_CONTENT_DIR = _CONTENT_DIR / "author"
AUTHOR_CONTENT_FILE = AUTHOR_CONTENT_DIR / "index.md"
HOMEPAGE_CONTENT_FILE = _CONTENT_DIR / "homepage.md"
META_CONTENT_FILE = _CONTENT_DIR / "meta.md"
POSTS_CONTENT_DIR = _CONTENT_DIR / "posts"
PROJECTS_CONTENT_DIR = _CONTENT_DIR / "projects"

# Static assets configuration
STATIC_DIR = _BASE_DIR / "app" / "static"
STATIC_PREFIX = "/static/"
_ANSI_DIR = _BASE_DIR / "app" / "ansi"

# Directories for images
IMAGES_DIR = STATIC_DIR / "images"
HEADERS_DIR = IMAGES_DIR / "headers"
THUMBNAILS_DIR = IMAGES_DIR / "thumbnails"

# Directories for ansi images
ANSI_IMAGES_DIR = _ANSI_DIR / "images"
ANSI_HEADERS_DIR = ANSI_IMAGES_DIR / "headers"
ANSI_THUMBNAILS_DIR = ANSI_IMAGES_DIR / "thumbnails"

# Relative references used in templates
STATIC_RELATIVE_DIR = STATIC_DIR
IMAGES_RELATIVE_DIR = IMAGES_DIR

# Template for cover images, zero-padded to 3 digits (e.g., cover_001.png)
COVER_FILENAME_TEMPLATE = "cover_{:03d}.png"
COVER_ANSI_FILENAME_TEMPLATE = "cover_{:03d}.ansi"
