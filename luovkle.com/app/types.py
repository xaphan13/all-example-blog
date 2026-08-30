from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from app.schemas import CoverUrls, PostANSIContent, ProjectANSIContent


class HeadersAndThumbnailsDict(TypedDict):
    headers: CoverUrls
    thumbnails: CoverUrls


class ANSIContent(TypedDict):
    posts: dict[str, PostANSIContent]
    projects: dict[str, ProjectANSIContent]


class TemplateArgsDict(TypedDict):
    code: bool


class ParsedMarkdownDict(TypedDict):
    content: str
    extras: TemplateArgsDict
