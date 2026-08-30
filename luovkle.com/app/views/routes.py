from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from app.services.ansi import get_ansi_content
from app.services.html import get_content
from app.views.deps import is_cli_client
from app.views.utils import is_cli_client_by_user_agent, render_ansi_template

if TYPE_CHECKING:
    from fastapi import FastAPI


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_content()
    get_ansi_content()
    yield


router = APIRouter(
    lifespan=lifespan,
    include_in_schema=False,
)

templates = Jinja2Templates(directory="app/templates/")


def post_html_detail(request: Request, slug: str):
    content = get_content()
    post = content["posts"].get(slug)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    context = {
        "metadata": content["metadata"],
        "author": content["author"],
        "post": post,
    }
    return templates.TemplateResponse(request, "post_detail.html", context=context)


def post_ansi_detail(slug: str):
    content = get_ansi_content()
    post = content["posts"].get(slug)
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    author = get_content()["author"]
    context = {"post": post, "author": author}
    return render_ansi_template("post_template", context)


def project_html_detail(request: Request, slug: str):
    content = get_content()
    project = content["projects"].get(slug)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    context = {
        "metadata": content["metadata"],
        "author": content["author"],
        "project": project,
    }
    return templates.TemplateResponse(request, "project_detail.html", context)


def project_ansi_detail(slug: str):
    content = get_ansi_content()
    project = content["projects"].get(slug)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND)
    author = get_content()["author"]
    context = {"project": project, "author": author}
    return render_ansi_template("project_template", context)


def cli_user_wrapper(func):
    def wrap(request: Request, status_code: int):
        if is_cli_client_by_user_agent(str(request.headers.get("User-Agent"))):
            if status_code == status.HTTP_404_NOT_FOUND:
                template = "not_found_template"
            else:
                template = "unexpected_error_template"
            return PlainTextResponse(
                render_ansi_template(template),
                status_code=status_code,
            )
        return func(request, status_code)

    return wrap


@cli_user_wrapper
def internal_exception(request: Request, status_code: int):
    content = get_content()
    context = {"metadata": content["metadata"]}
    return templates.TemplateResponse(
        request,
        "500.html",
        context=context,
        status_code=status_code,
    )


@cli_user_wrapper
def not_found_exception(request: Request, status_code: int):
    content = get_content()
    context = {"metadata": content["metadata"]}
    return templates.TemplateResponse(
        request,
        "404.html",
        context=context,
        status_code=status_code,
    )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    content = get_content()
    context = {
        "metadata": content["metadata"],
        "author": content["author"],
        "homepage": content["homepage"],
    }
    return templates.TemplateResponse(request, "homepage.html", context)


@router.get("/p", response_class=HTMLResponse)
async def post_list(
    request: Request,
    cli_client: Annotated[bool, Depends(is_cli_client)],
):
    if cli_client:
        posts = [post.model_dump() for post in get_ansi_content()["posts"].values()]
        context = {"posts": []}
        for post in posts:
            post["url"] = str(request.url_for("post_detail", slug=post["slug"]))
            context["posts"].append(post)
        return render_ansi_template("post_list_template", context)
    content = get_content()
    posts = list(content["posts"].values())
    context = {
        "metadata": content["metadata"],
        "posts": posts,
    }
    return templates.TemplateResponse(request, "post_list.html", context)


@router.get("/p/{slug}", response_class=HTMLResponse)
async def post_detail(
    request: Request,
    slug: str,
    cli_client: Annotated[bool, Depends(is_cli_client)],
):
    if cli_client:
        return post_ansi_detail(slug)
    return post_html_detail(request, slug)


@router.get("/pr", response_class=HTMLResponse)
async def project_list(
    request: Request,
    cli_client: Annotated[bool, Depends(is_cli_client)],
):
    if cli_client:
        projects = [
            project.model_dump() for project in get_ansi_content()["projects"].values()
        ]
        context = {"projects": []}
        for project in projects:
            project["url"] = str(
                request.url_for("project_detail", slug=project["slug"])
            )
            context["projects"].append(project)
        return render_ansi_template("project_list_template", context)
    content = get_content()
    projects = list(content["projects"].values())
    context = {
        "metadata": content["metadata"],
        "projects": projects,
    }
    return templates.TemplateResponse(request, "project_list.html", context)


@router.get("/pr/{slug}", response_class=HTMLResponse)
async def project_detail(
    request: Request,
    slug: str,
    cli_client: Annotated[bool, Depends(is_cli_client)],
):
    if cli_client:
        return project_ansi_detail(slug)
    return project_html_detail(request, slug)


@router.get("/author", response_class=HTMLResponse)
async def author(request: Request):
    content = get_content()
    author = content["author"]
    context = {
        "metadata": content["metadata"],
        "author": author,
    }
    return templates.TemplateResponse(request, "author.html", context)


@router.head("/health", status_code=status.HTTP_204_NO_CONTENT)
async def health(): ...
