from functools import cache
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from app.config import (
    ANSI_HEADERS_DIR,
    ANSI_THUMBNAILS_DIR,
    COVER_ANSI_FILENAME_TEMPLATE,
    POSTS_CONTENT_DIR,
    PROJECTS_CONTENT_DIR,
)
from app.schemas import (
    ContentContext,
    GenericANSIContent,
    PostANSIContent,
    ProjectANSIContent,
)
from app.services.common import (
    estimate_reading_time,
    get_content_context,
    get_content_objects,
    get_cover_number,
    get_creation_date,
    get_slug,
    load_markdown_content,
    move_image,
)
from app.types import ANSIContent


def get_ansi_cover_path(title: str, cover_dir: Path) -> Path:
    number_of_covers = len(list(cover_dir.glob("*.ansi")))
    cover_number = get_cover_number(len(title), number_of_covers)
    cover_file = COVER_ANSI_FILENAME_TEMPLATE.format(cover_number)
    return cover_dir / cover_file


def render_markdown_to_ansi(md_content: str, width: int = 79) -> str:
    console = Console(
        width=width, record=True, force_terminal=True, color_system="truecolor"
    )
    with console.capture() as cap:
        console.print(Markdown(md_content, code_theme="github-dark"))
    return cap.get()


def _truncate_with_ellipsis(text: str, max_length: int) -> str:
    """Append an ellipsis while keeping the result within max_length.

    If the text plus the ellipsis exceeds max_length, the text is shortened
    before appending the ellipsis.

    Args:
        text (str): Text to shorten.
        max_length (int): Maximum length allowed for the returned text.

    Returns:
        str: Text ending in ``...`` with a length no greater than max_length.
    """
    diff = max_length - (len(text) + 3)
    if diff >= 0:
        return text.strip() + "..."
    return text[:diff].strip() + "..."


def _partition_text_at_word_boundary(text: str, max_length: int) -> tuple[str, str]:
    """Split text into a fitting prefix and the remaining text.

    The prefix is split at the last space before max_length so words are not
    cut in the middle.

    Args:
        text (str): Text to split.
        max_length (int): Maximum length allowed for the first returned part.

    Returns:
        tuple[str, str]: A tuple containing the text that fits and the
            remaining text.
    """
    stripped_text = text.strip()
    if len(stripped_text) <= max_length:
        return stripped_text, ""
    # Find the last safe split point so the first part does not cut a word.
    last_space_idx = 0
    for idx, char in enumerate(stripped_text):
        if idx > max_length:
            break
        if char == " " and last_space_idx < max_length:
            last_space_idx = idx
    return stripped_text[:last_space_idx], stripped_text[last_space_idx:]


def _wrap_and_truncate_text(text: str, max_lines: int, max_length: int) -> list[str]:
    """Wrap text into a limited number of lines.

    Lines are split at word boundaries when possible. If there is still text
    left after reaching max_lines, the last line is truncated with an ellipsis.

    Args:
        text (str): Text to wrap.
        max_lines (int): Maximum number of lines to return.
        max_length (int): Maximum length allowed for each line.

    Returns:
        list[str]: A list of wrapped lines.
    """
    text = text.strip()
    # A single oversized word cannot be wrapped by word boundaries.
    if len(text) > max_length and len(text.split()) == 1:
        return [_truncate_with_ellipsis(text, max_length)]
    lines: list[str] = []
    for current_line_number in range(1, max_lines + 1):
        if len(text) == 0:
            break
        line, text = _partition_text_at_word_boundary(text, max_length)
        # Mark the final allowed line as incomplete when text remains.
        if current_line_number == max_lines and len(text) > 0:
            line = _truncate_with_ellipsis(line, max_length)
        lines.append(line)
    return lines


def _format_ansi_description_lines(
    description: str | None = None,
    line_count: int = 2,
) -> list[str]:
    """Format a description for ANSI output using a fixed number of lines.

    The description is wrapped and truncated when needed, then padded with
    empty strings so the result always contains exactly line_count items.

    Args:
        description (str | None): Description text to format.
        line_count (int): Exact number of lines to return.

    Returns:
        list[str]: Wrapped description lines padded to line_count.
    """
    wrapped_description_lines = _wrap_and_truncate_text(
        description or "", line_count, 35
    )
    missing_line_count = line_count - len(wrapped_description_lines)
    wrapped_description_lines.extend([""] * missing_line_count)
    return wrapped_description_lines


def _get_generic_ansi_content(
    content_context: ContentContext,
) -> GenericANSIContent:
    index_path: Path = content_context.index_file
    if not index_path.is_file():
        raise FileNotFoundError(f"index file not found: {index_path!s}")
    # If the context provides images, copy them into the static images directory.
    if content_context.img_files:
        move_image(content_context)
    # Load markdown content and metadata from the source file
    markdown_content = load_markdown_content(content_context.index_file)
    # Parse markdown only if a body exists; otherwise use safe defaults
    if markdown_content.body:
        body = render_markdown_to_ansi(markdown_content.body)
    else:
        body = None
    # Resolve derived fields and fallbacks
    slug = markdown_content.slug or get_slug(content_context.index_file)
    reading_time_minutes = estimate_reading_time(markdown_content.body)
    publish_date = markdown_content.date or get_creation_date(
        content_context.index_file
    )
    header_path = get_ansi_cover_path(markdown_content.title, ANSI_HEADERS_DIR)
    header = header_path.read_text(encoding="utf-8")
    thumbnail_path = get_ansi_cover_path(markdown_content.title, ANSI_THUMBNAILS_DIR)
    thumbnail = thumbnail_path.read_text(encoding="utf-8")
    # Assemble final payload for the published content model
    return GenericANSIContent(
        slug=slug,
        header=header,
        thumbnail=thumbnail,
        title=markdown_content.title,
        publish_date=publish_date,
        body=body,
        reading_time_minutes=reading_time_minutes,
        description=markdown_content.description,
        repository=markdown_content.repository,
        website=markdown_content.website,
        topic=markdown_content.topic,
    )


def _get_post_ansi_content(content_context: ContentContext) -> PostANSIContent:
    generic_ansi_content = _get_generic_ansi_content(content_context)
    return PostANSIContent(**generic_ansi_content.model_dump())


def _get_project_ansi_content(
    content_context: ContentContext,
) -> ProjectANSIContent:
    generic_ansi_content = _get_generic_ansi_content(content_context)
    return ProjectANSIContent(**generic_ansi_content.model_dump())


def get_posts_content() -> dict[str, PostANSIContent]:
    posts: dict[str, PostANSIContent] = {}
    for content_obj in get_content_objects(POSTS_CONTENT_DIR):
        content_context = get_content_context(content_obj)
        content = _get_post_ansi_content(content_context)
        posts[content.slug] = content
    return posts


def get_projects_content() -> dict[str, ProjectANSIContent]:
    projects: dict[str, ProjectANSIContent] = {}
    for content_obj in get_content_objects(PROJECTS_CONTENT_DIR):
        content_context = get_content_context(content_obj)
        content = _get_project_ansi_content(content_context)
        content.ansi_description = _format_ansi_description_lines(content.description)
        projects[content.slug] = content
    return projects


@cache
def get_ansi_content() -> ANSIContent:
    return {"posts": get_posts_content(), "projects": get_projects_content()}
