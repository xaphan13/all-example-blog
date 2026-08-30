import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from app.config import IMAGES_DIR
from app.schemas import ContentContext, MarkdownContent


def get_slug(md_file: Path) -> str:
    file = md_file.name
    return file.removesuffix(".md").replace("_", "-")


def estimate_reading_time(content: str | None = None) -> int:
    # number of words in an post / 200 words per minute
    if not content:
        return 0
    return round(len(content.split()) / 200)


def get_creation_date(md_file: Path) -> str:
    c_time = os.path.getctime(md_file)
    return datetime.fromtimestamp(c_time).strftime("%d.%m.%Y")


def get_cover_number(n: int, max: int) -> int:
    if n > max:
        return get_cover_number(n - max, max)
    return n


def split_markdown_file(md_content: str) -> tuple[str, str]:
    metadata_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
    match = re.match(metadata_pattern, md_content, re.DOTALL)
    if not match:
        raise ValueError("Could not find the metadata in the markdown file")
    return match.group(1), match.group(2)


def move_image(
    content_context: ContentContext, force_overwrite: bool = False
) -> list[Path]:
    """Copy image assets from `<dir>/images` into the static images tree.

    If the destination directory already exists and `force_overwrite` is False,
    the function does not copy anything and returns the expected destination
    paths based on the source filenames.

    Note:
        The function name says "move", but the operation performed is a copy
        (`shutil.copy`). If true moving is desired, replace copy with move.

    Args:
        content_context: A ContentContext referencing the `index_file` and the
            content type.
        force_overwrite: If True, rebuild the destination directory and copy
            images even if the destination already exists.

    Returns:
        A list of destination Paths for the copied images (or the expected
        destination paths when skipping the copy).

    Raises:
        NotADirectoryError: If the base content directory is invalid or if
            `images` is not a directory.
        FileNotFoundError: If the images directory is missing or if there are
            no files to copy.
        ValueError: If the destination path is an unsupported type.
        OSError: For underlying filesystem errors (permissions, locks, etc.).
    """
    # Resolve the directory that contains the index file.
    directory = content_context.index_file.parent
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a valid directory")
    images_content_dir = directory / "images"
    if not images_content_dir.exists():
        raise FileNotFoundError(f"Missing images directory: {images_content_dir}")
    if images_content_dir.exists() and not images_content_dir.is_dir():
        raise NotADirectoryError(
            f"'{images_content_dir.name}' exists but is not a directory"
        )
    # Find files (non-recursive) to copy from the source images directory.
    image_content_items = list(images_content_dir.iterdir())
    if not image_content_items:
        raise FileNotFoundError(f"No image files found in {images_content_dir}")
    # Destination: /static/images/<content_type>/<dir_name>
    images_static_dir = IMAGES_DIR / content_context.content_type / directory.name
    # If the destination already exists and overwrite is disabled, skip copying
    # and return the expected destination paths.
    if images_static_dir.exists() and not force_overwrite:
        return [Path(images_static_dir / src.name) for src in image_content_items]
    # If the destination exists, remove it to ensure a clean state.
    if images_static_dir.exists():
        if images_static_dir.is_dir():
            shutil.rmtree(images_static_dir)
        elif images_static_dir.is_file():
            images_static_dir.unlink()
        else:
            raise ValueError(f"Unsupported path type: {images_static_dir!s}")
    # Create a fresh destination directory (with parents).
    images_static_dir.mkdir(parents=True, exist_ok=False)
    # Copy images to the destination. Track destination paths for the return.
    dst_paths: list[Path] = []
    for src in image_content_items:
        dst = images_static_dir / src.name
        copied_path_str = shutil.copy(src, dst)
        dst_paths.append(Path(copied_path_str))
    return dst_paths


def get_content_objects(directory: Path) -> list[Path]:
    """Enumerate content objects inside a directory.

    A content object can be either:
    - A subdirectory (expected to contain an `index.md`).
    - A Markdown file with the `.md` suffix.

    Args:
        directory: Directory to scan.

    Returns:
        A list of Paths representing either subdirectories or `.md` files.

    Raises:
        NotADirectoryError: If `directory` is not a directory.
        ValueError: If an entry is a file without `.md` extension or if it has an
            unsupported type.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f"{directory} is not a valid directory")
    content: list[Path] = []
    for path in directory.iterdir():
        # Accept nested directories as potential content containers.
        if path.is_dir():
            content.append(path)
        # Accept only Markdown files when the entry is a file.
        elif path.is_file():
            if not path.suffix == ".md":
                raise ValueError(f"Invalid file type: {path.name}")
            content.append(path)
        else:
            # Reject special file types (symlinks to sockets, fifos, etc.).
            raise ValueError(f"Unsupported path type: {path!s}")
    return content


def get_content_context(path: Path) -> ContentContext:
    """Build a ContentContext from a path to a directory or a Markdown file.

    For directories, this expects:
    - An `index.md` inside the directory.
    - An optional `images/` subdirectory with assets.

    Args:
        path: Path to a content directory or a Markdown file.

    Returns:
        A ContentContext with the resolved index file and optional images list.

    Raises:
        FileNotFoundError: If `path` doesn't exist or `index.md` is missing.
        NotADirectoryError: If `images` exists but is not a directory.
        ValueError: If `path` is neither a directory nor a `.md` file.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe: {path!s}")
    if path.is_dir():
        index_file = path / "index.md"
        if not index_file.is_file():
            raise FileNotFoundError(index_file)
        images_dir = path / "images"
        # If an `images` path exists, validate it is a directory.
        if images_dir.exists() and not images_dir.is_dir():
            raise NotADirectoryError(
                f"'{images_dir.name}' exists but is not a directory"
            )
        img_files = list(images_dir.iterdir()) if images_dir.is_dir() else None
        # The `content_type` is inferred from the parent directory's name.
        return ContentContext(
            index_file=index_file,
            img_files=img_files,
            is_dir=True,
            content_type=path.parent.stem,
        )
    if path.is_file():
        if not path.suffix == ".md":
            raise ValueError(f"Invalid file type: {path.name}")
        return ContentContext(index_file=path, content_type=path.parent.stem)
    # Unsupported path types are explicitly rejected.
    raise ValueError(f"Unsupported path type: {path!s}")


def load_generic_markdown_content(md_file: Path) -> dict[str, Any]:
    md_content = md_file.read_text(encoding="utf-8")
    raw_metadata, raw_body = split_markdown_file(md_content)
    metadata = yaml.safe_load(raw_metadata)
    if not metadata:
        raise KeyError("No properties found in metadata")
    return {**metadata, "body": raw_body}


def load_markdown_content(md_file: Path) -> MarkdownContent:
    generic_markdown_content = load_generic_markdown_content(md_file)
    return MarkdownContent(**generic_markdown_content)
