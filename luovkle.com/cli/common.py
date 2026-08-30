import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

OutputFileExtension = Literal[".ansi", ".webp", ".avif"]


def get_input_paths(images_dir: Path) -> list[Path]:
    """Return all `.png` and `.jpeg` image paths within a directory.

    Args:
        images_dir (Path): Directory containing input images.

    Returns:
        list[Path]: List of image paths.
    """
    patterns = ("**/*.png", "**/*.jpeg")
    paths = []
    for pattern in patterns:
        paths.extend(list(images_dir.glob(pattern)))
    return paths


def get_output_paths(
    input_paths: list[Path],
    output_file_extension: OutputFileExtension,
    output_dir: Path | None = None,
) -> list[Path]:
    """Build output file paths for given inputs.

    Args:
        input_paths (list[Path]): Input image paths.
        output_file_extension (OutputFileExtension): Output file extension.
        output_dir (Path | None, optional): Target directory. Defaults to same as input.

    Returns:
        list[Path]: Output file paths.
    """
    output_paths = []
    for input_path in input_paths:
        output_path = output_dir or input_path.parent
        output_paths.append(output_path / (input_path.stem + output_file_extension))
    return output_paths


async def run_blocking_tasks_in_threads(
    funcs_and_args: list[tuple[Callable, tuple]],
) -> None:
    """Execute blocking functions concurrently using threads.

    Args:
        funcs_and_args (list[tuple[Callable, tuple]]): List of (function, args) pairs.
    """
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as executor:
        tasks = [
            loop.run_in_executor(executor, func, *args) for func, args in funcs_and_args
        ]
        await asyncio.gather(*tasks, return_exceptions=False)


def get_tasks(fn: Callable, io_paths: list[tuple]) -> list[tuple[Callable, tuple]]:
    return [(fn, paths) for paths in io_paths]
