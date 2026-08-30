import asyncio
from pathlib import Path

from PIL import Image

from cli.common import (
    get_input_paths,
    get_output_paths,
    get_tasks,
    run_blocking_tasks_in_threads,
)
from cli.config import ANSI_HEADERS_DIR, ANSI_THUMBNAILS_DIR, HEADERS_DIR

if not ANSI_HEADERS_DIR.is_dir():
    ANSI_HEADERS_DIR.mkdir(parents=True)

if not ANSI_THUMBNAILS_DIR.is_dir():
    ANSI_THUMBNAILS_DIR.mkdir(parents=True)


def img_to_ansi(input_path: Path, output_path: Path, width: int = 79) -> None:
    """Convert an image to colored ANSI art and save it as text.

    Args:
        input_path (Path): Source image path.
        output_path (Path): Destination `.ansi` text file path.
        width (int, optional): Target width in characters. Defaults to 79.

    Raises:
        OSError: If pixel data cannot be accessed.

    Returns:
        None

    Notes:
        Uses 24-bit ANSI (ESC[38;2;r;g;bm) with a full block (█) per pixel.
    """
    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    aspect = h / w
    # Vertical correction factor to compensate for character height in terminals
    img = img.resize((width, int(width * aspect * 0.3)))
    pixels = img.load()
    if pixels is None:
        raise OSError("Error accessing pixel data.")
    lines = []
    for y in range(img.height):
        line = ""
        for x in range(img.width):
            r, g, b = pixels[x, y]  # type: ignore
            # Represent each pixel as a colored ANSI block
            line += f"\033[38;2;{r};{g};{b}m█"
        line += "\033[0m"  # Reset ANSI color at end of line
        lines.append(line)
    output_path.write_text("\n".join(lines))


async def main() -> None:
    # Collect all source image paths and matching ANSI output paths
    input_paths = get_input_paths(HEADERS_DIR)
    # Generate ANSI headers
    ansi_headers_io_paths = list(
        zip(
            input_paths,
            get_output_paths(input_paths, ".ansi", ANSI_HEADERS_DIR),
            strict=False,
        )
    )
    tasks = get_tasks(img_to_ansi, ansi_headers_io_paths)
    await run_blocking_tasks_in_threads(tasks)
    # Generate ANSI thumbnails
    ansi_thumbnails_io_paths = list(
        zip(
            input_paths,
            get_output_paths(input_paths, ".ansi", ANSI_THUMBNAILS_DIR),
            [40] * len(input_paths),
            strict=False,
        )
    )
    tasks = get_tasks(img_to_ansi, ansi_thumbnails_io_paths)
    await run_blocking_tasks_in_threads(tasks)


if __name__ == "__main__":
    asyncio.run(main())
