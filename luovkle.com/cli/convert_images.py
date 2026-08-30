import asyncio
from pathlib import Path

from PIL import Image

from cli.common import (
    get_input_paths,
    get_output_paths,
    get_tasks,
    run_blocking_tasks_in_threads,
)
from cli.config import IMAGES_DIR


def img_to_webp(
    input_path: Path,
    output_path: Path,
    force_overwrite: bool = False,
    save_if_smaller: bool = True,
) -> None:
    """Convert an image to lossless WebP format.

    Args:
        input_path (Path): Source image path.
        output_path (Path): Output `.webp` path.
        force_overwrite (bool, optional): Overwrite if exists. Defaults to False.
        save_if_smaller (bool, optional): Keep if smaller. Defaults to True.
    """
    if not force_overwrite and output_path.exists():
        return None
    img = Image.open(input_path).convert("RGBA")
    img.save(output_path, format="WEBP", lossless=True)
    if save_if_smaller and output_path.stat().st_size >= input_path.stat().st_size:
        output_path.unlink()


def img_to_avif(
    input_path: Path,
    output_path: Path,
    force_overwrite: bool = False,
    save_if_smaller: bool = True,
) -> None:
    """Convert an image to high-quality AVIF format.

    Args:
        input_path (Path): Source image path.
        output_path (Path): Output `.avif` path.
        force_overwrite (bool, optional): Overwrite if exists. Defaults to False.
        save_if_smaller (bool, optional): Keep if smaller. Defaults to True.
    """
    if not force_overwrite and output_path.exists():
        return None
    img = Image.open(input_path).convert("RGBA")
    img.save(
        output_path,
        format="AVIF",
        quality=90,
        chroma_subsampling="444",
        range="full",
        speed=4,
    )
    if save_if_smaller and output_path.stat().st_size >= input_path.stat().st_size:
        output_path.unlink()


async def main() -> None:
    input_paths = get_input_paths(IMAGES_DIR)
    # Convert to WebP
    webp_io_paths = list(
        zip(input_paths, get_output_paths(input_paths, ".webp"), strict=False)
    )
    tasks = get_tasks(img_to_webp, webp_io_paths)
    await run_blocking_tasks_in_threads(tasks)
    # Convert to AVIF
    avif_io_paths = list(
        zip(input_paths, get_output_paths(input_paths, ".avif"), strict=False)
    )
    tasks = get_tasks(img_to_avif, avif_io_paths)
    await run_blocking_tasks_in_threads(tasks)


if __name__ == "__main__":
    asyncio.run(main())
