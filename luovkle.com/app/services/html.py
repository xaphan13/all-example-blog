from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

import markdown
from bs4 import BeautifulSoup

from app.config import (
    AUTHOR_CONTENT_DIR,
    AUTHOR_CONTENT_FILE,
    COVER_FILENAME_TEMPLATE,
    HEADERS_DIR,
    HOMEPAGE_CONTENT_FILE,
    IMAGES_DIR,
    IMAGES_RELATIVE_DIR,
    META_CONTENT_FILE,
    POSTS_CONTENT_DIR,
    PROJECTS_CONTENT_DIR,
    STATIC_PREFIX,
    STATIC_RELATIVE_DIR,
    THUMBNAILS_DIR,
)
from app.schemas import (
    AuthorMD,
    ContentContext,
    CoverUrls,
    HomepageMD,
    MetadataMD,
    PublishedContent,
)
from app.services.common import (
    estimate_reading_time,
    get_content_context,
    get_content_objects,
    get_cover_number,
    get_creation_date,
    get_slug,
    load_generic_markdown_content,
    load_markdown_content,
    move_image,
)
from app.types import HeadersAndThumbnailsDict, ParsedMarkdownDict, TemplateArgsDict


def get_alternative_file_formats(original_file_path: Path) -> dict[str, Path]:
    alt_files = {}
    for suffix in ("avif", "webp"):
        alt_file = original_file_path.with_suffix(f".{suffix}")
        if alt_file.is_file():
            alt_files[suffix] = alt_file
    return alt_files


def collect_relative_image_urls(
    default_path: Path,
    alternative_paths: dict[str, Path],
) -> "CoverUrls":
    cover_paths = {"default": default_path, **alternative_paths}
    cover_urls: dict[str, Path] = {}
    for name, path in cover_paths.items():
        cover_urls[name] = path.relative_to(STATIC_RELATIVE_DIR)
    return CoverUrls(**cover_urls)


def _get_cover_urls(covers_path: Path, title: str) -> "CoverUrls":
    #
    number_of_covers = len(list(covers_path.glob("*.png")))
    cover_number = get_cover_number(len(title), number_of_covers)
    cover_file = COVER_FILENAME_TEMPLATE.format(cover_number)
    #
    default_cover_path = covers_path / cover_file
    alt_cover_paths = get_alternative_file_formats(default_cover_path)
    return collect_relative_image_urls(default_cover_path, alt_cover_paths)


def get_headers_and_thumbnails(title: str) -> HeadersAndThumbnailsDict:
    return {
        "headers": _get_cover_urls(HEADERS_DIR, title),
        "thumbnails": _get_cover_urls(THUMBNAILS_DIR, title),
    }


def copy_pictures_to_static_dir(picture_content_path: Path) -> Path:
    picture_parent, picture = picture_content_path.parts[-2:]
    static_path = IMAGES_RELATIVE_DIR / picture_parent
    if not static_path.is_dir():
        static_path.mkdir()
    picture_static_path = static_path / picture
    if not picture_static_path.exists():
        picture_static_path.write_bytes(picture_content_path.read_bytes())
    return picture_static_path


def _is_external_url(src: str) -> bool:
    """Determine whether the given string is an absolute (external) URL.

    An external URL is considered one that includes a scheme (e.g., http/https),
    and:
      - has a network location (netloc), or
      - uses a scheme like `data:` or `mailto:` which is absolute by definition.

    Args:
        src: URL or path string to evaluate.

    Returns:
        True if `src` is an absolute/external URL, otherwise False.

    Raises:
        ValueError: If `src` is not a string or is empty/whitespace.
    """
    if type(src) is not str:
        raise ValueError(f"Expected a string, got {type(src).__name__!r}")
    if not src.strip():
        raise ValueError("URL source cannot be empty or only whitespace")
    parts = urlsplit(src)
    if parts.scheme:
        if parts.netloc or parts.scheme in {"data", "mailto"}:
            return True
    return False


def _parse_markdown(content_context: ContentContext, body: str) -> ParsedMarkdownDict:
    # Convert Markdown to HTML (no extra extensions enabled here by design).
    html_content = markdown.markdown(
        body,
        extensions=["fenced_code", "codehilite"],
        output_format="html",
    )
    template_args: TemplateArgsDict = {"code": False}
    # Parse rendered HTML to find and rewrite image sources when they are local.
    soup = BeautifulSoup(html_content, "html.parser")
    imgs = soup.find_all("img")
    # Use the directory containing the index file to compute a unique static path.
    directory = content_context.index_file.parent
    for img in imgs:
        img_src_raw = img.get("src")
        img_src_str = str(img_src_raw)  # Normalize to string for checks.
        # Skip empty sources or external URLs (keep as-is).
        if not img_src_raw or _is_external_url(img_src_str):
            continue
        # Only use the filename part to avoid leaking nested relative paths.
        src_name = Path(img_src_str).name
        # Destination: /static/images/<content_type>/<dir_name>/<src_name>
        dest = IMAGES_DIR / content_context.content_type / directory.name / src_name
        # Generate a path relative to the static root to feed url_for().
        rel = STATIC_PREFIX + str(dest.relative_to(STATIC_RELATIVE_DIR).as_posix())
        # Inject a Jinja expression that FastAPI will resolve at render time.
        img["src"] = rel
    # Check for <code> tags
    code_blocks = soup.find_all("code")
    if len(code_blocks) >= 1:
        template_args["code"] = True
    # Update <a> tags
    tags = soup.find_all("a")
    for tag in tags:
        tag.attrs["class"] = "text-sky-500 font-bold"
        tag.attrs["target"] = "_blank"
        tag.attrs["rel"] = "noopener noreferrer"
    # Update <h1> tags
    for tag in soup.find_all("h1"):
        tag.attrs["class"] = "text-4xl font-black"
    # Update <h2> tags
    for tag in soup.find_all("h2"):
        tag.attrs["class"] = "text-3xl font-black"
    # Update <h3> tags
    for tag in soup.find_all("h3"):
        tag.attrs["class"] = "text-2xl font-black"
    # Update <h4> tags
    for tag in soup.find_all("h4"):
        tag.attrs["class"] = "text-xl font-black"
    # Update <h5> tags
    for tag in soup.find_all("h5"):
        tag.attrs["class"] = "text-xl font-bold"
    # Update <h6> tags
    for tag in soup.find_all("h6"):
        tag.attrs["class"] = "text-lg font-bold"
    # Update <blockquote> tags
    for tag in soup.find_all("blockquote"):
        tag.attrs["class"] = (
            "bg-neutral-900 px-4 py-2 italic rounded-md text-base font-medium"
        )
    # Update <ul> tags
    for tag in soup.find_all("ul"):
        tag.attrs["class"] = "ps-5 space-y-1 list-disc list-inside"
    # Update <li> tags
    for tag in soup.find_all("ol"):
        tag.attrs["class"] = "ps-5 space-y-1 list-decimal list-inside"
    # Update <img> tags
    for tag in soup.find_all("img"):
        tag.attrs["class"] = "mx-auto"
    # Update <pre> tags
    for tag in soup.find_all("pre"):
        tag.attrs["class"] = "py-3 px-3 text-md overflow-x-auto"
    return {"content": str(soup), "extras": template_args}


def _get_published_content(content_context: ContentContext) -> PublishedContent:
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
        parsed_markdown = _parse_markdown(content_context, markdown_content.body)
        body, extras = parsed_markdown["content"], parsed_markdown["extras"]
    else:
        body = None
        extras: TemplateArgsDict = {"code": False}
    # Resolve derived fields and fallbacks
    slug = markdown_content.slug or get_slug(content_context.index_file)
    headers_and_thumbnails = get_headers_and_thumbnails(markdown_content.title)
    cover_image_path = headers_and_thumbnails["headers"].default
    thumbnail_path = headers_and_thumbnails["thumbnails"].default
    reading_time_minutes = estimate_reading_time(markdown_content.body)
    publish_date = markdown_content.date or get_creation_date(
        content_context.index_file
    )
    # Assemble final payload for the published content model
    return PublishedContent(
        title=markdown_content.title,
        description=markdown_content.description,
        repository=markdown_content.repository,
        website=markdown_content.website,
        slug=slug,
        topic=markdown_content.topic,
        body=body,
        thumbnail_path=thumbnail_path,
        cover_image_path=cover_image_path,
        reading_time_minutes=reading_time_minutes,
        publish_date=publish_date,
        extras=extras,
    )


def get_metadata_content():
    generic_markdown_content = load_generic_markdown_content(META_CONTENT_FILE)
    metadata_md = MetadataMD(**generic_markdown_content)
    headers_and_thumbnails = get_headers_and_thumbnails(metadata_md.author)
    default_thumbnail = headers_and_thumbnails["thumbnails"].default_url
    return {
        **metadata_md.model_dump(),
        "og_image": metadata_md.og_image or default_thumbnail,
        "twitter_image": metadata_md.twitter_image or default_thumbnail,
    }


def get_author_content():
    generic_markdown_content = load_generic_markdown_content(AUTHOR_CONTENT_FILE)
    author_md = AuthorMD(**generic_markdown_content)
    picture_content_path = AUTHOR_CONTENT_DIR / author_md.picture
    picture_path = copy_pictures_to_static_dir(picture_content_path)
    alt_picture_paths = get_alternative_file_formats(picture_path)
    return {
        **author_md.model_dump(),
        "picture": collect_relative_image_urls(picture_path, alt_picture_paths),
    }


def get_posts_content():
    posts = {}
    for content_obj in get_content_objects(POSTS_CONTENT_DIR):
        content_context = get_content_context(content_obj)
        content = _get_published_content(content_context)
        posts[content.slug] = content.model_dump()
    return posts


def get_projects_content():
    projects = {}
    for content_obj in get_content_objects(PROJECTS_CONTENT_DIR):
        content_context = get_content_context(content_obj)
        content = _get_published_content(content_context)
        projects[content.slug] = content.model_dump()
    return projects


def get_homepage_data(posts_data, projects_data):
    generic_markdown_content = load_generic_markdown_content(HOMEPAGE_CONTENT_FILE)
    homepage_md = HomepageMD(**generic_markdown_content)
    posts_headers_and_thumbnails = get_headers_and_thumbnails("posts")
    projects_headers_and_thumbnails = get_headers_and_thumbnails("projects")
    return {
        "posts_section": {
            "description": homepage_md.posts_section_description,
            "entries": str(len(posts_data)),
            "thumbnail": posts_headers_and_thumbnails["thumbnails"],
        },
        "projects_section": {
            "description": homepage_md.projects_section_description,
            "entries": str(len(projects_data)),
            "thumbnail": projects_headers_and_thumbnails["thumbnails"],
        },
    }


@cache
def get_content():
    data = {
        "metadata": get_metadata_content(),
        "author": get_author_content(),
        "posts": get_posts_content(),
        "projects": get_projects_content(),
    }
    data["homepage"] = get_homepage_data(data["posts"], data["projects"])
    return data
