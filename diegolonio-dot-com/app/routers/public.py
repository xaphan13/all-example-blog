"""Rutas públicas del sitio."""

from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import PlainTextResponse, Response

from app.config import settings
from app.database import get_db
from app.projects import load_projects
from app.queries import posts, tags
from app.templating import templates

router = APIRouter()

# Entradas por página en el inicio
POSTS_PER_PAGE = 6


@router.get("/about")
def about(request: Request):
    # Página About: bio, tech stack y proyectos curados en projects.yaml
    return templates.TemplateResponse(
        request, "about.html", {"projects": load_projects()}
    )


@router.get("/")
def home(request: Request, page: int = 1, db=Depends(get_db)):
    # Páginas inválidas (<1) se tratan como la primera
    if page < 1:
        page = 1

    total = posts.count_published(db)
    total_pages = max(1, ceil(total / POSTS_PER_PAGE))

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "posts": posts.list_published(
                db, POSTS_PER_PAGE, (page - 1) * POSTS_PER_PAGE
            ),
            "page": page,
            "total_pages": total_pages,
            "has_prev": page > 1,
            "has_next": page < total_pages,
        },
    )


@router.get("/robots.txt")
def robots():
    content = (
        "User-agent: *\n"
        "Disallow: /admin\n"
        "\n"
        f"Sitemap: {settings.base_url}/sitemap.xml\n"
    )
    return PlainTextResponse(content)


@router.get("/sitemap.xml")
def sitemap(db=Depends(get_db)):
    """Sitemap con las páginas fijas y todas las entradas publicadas."""
    entries = [f"<url><loc>{settings.base_url}/</loc></url>",
               f"<url><loc>{settings.base_url}/about</loc></url>"]
    for post in posts.list_published(db, limit=1000, offset=0):
        lastmod = post["published_at"].date().isoformat()
        entries.append(
            f"<url><loc>{settings.base_url}/post/{post['slug']}</loc>"
            f"<lastmod>{lastmod}</lastmod></url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + "\n</urlset>\n"
    )
    return Response(content=xml, media_type="application/xml")


@router.get("/post/{slug}")
def post_detail(request: Request, slug: str, db=Depends(get_db)):
    post = posts.get_published_by_slug(db, slug)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return templates.TemplateResponse(
        request,
        "post.html",
        {
            "post": post,
            "post_tags": tags.list_for_post(db, post["id"]),
            "prev_post": posts.get_prev(db, post["published_at"]),
            "next_post": posts.get_next(db, post["published_at"]),
        },
    )


@router.get("/tags/{slug}")
def tag_detail(request: Request, slug: str, db=Depends(get_db)):
    tag = tags.get_by_slug(db, slug)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    return templates.TemplateResponse(
        request,
        "tag.html",
        {
            "tag": tag,
            "posts": posts.list_published_by_tag(db, slug),
        },
    )


@router.get("/search")
def search(request: Request, q: str = "", db=Depends(get_db)):
    # Sin consulta se muestra solo el formulario (results=None)
    results = posts.search(db, q) if q else None

    return templates.TemplateResponse(
        request,
        "search.html",
        {"q": q, "results": results},
    )
