"""Rutas del panel de administración."""

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.auth import (
    COOKIE_NAME,
    create_session_token,
    get_session_username,
    require_admin,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.markdown_render import render_markdown
from app.media_cleanup import delete_orphans
from app.queries import posts, tags, users
from app.slugs import make_slug, unique_slug
from app.templating import templates

router = APIRouter(prefix="/admin")


def _save_tags(db, post_id: int, tags_str: str):
    """'ML, Deep Learning' → crea los tags que falten y los asigna al post."""
    tag_ids = []
    for name in tags_str.split(","):
        # Minúsculas siempre: los chips del editor ya las mandan así, pero
        # el form debe normalizar igual aunque el JS no cargue
        name = name.strip().lower()
        if name:
            tag = tags.get_or_create(db, name, make_slug(name))
            # Evita duplicados: "ML" y "ml" resuelven al mismo tag
            if tag["id"] not in tag_ids:
                tag_ids.append(tag["id"])
    tags.set_for_post(db, post_id, tag_ids)


# --- Login / logout ---------------------------------------------------------

@router.get("/login")
def login_form(request: Request):
    if get_session_username(request):
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse(request, "admin/login.html", {})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(),
    password: str = Form(),
    db=Depends(get_db),
):
    user = users.get_by_username(db, username)
    if user is None or not verify_password(user["password_hash"], password):
        return templates.TemplateResponse(
            request,
            "admin/login.html",
            {"error": "Invalid username or password"},
            status_code=401,
        )

    response = RedirectResponse("/admin", status_code=303)
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(username),
        max_age=settings.session_max_age,
        httponly=True,   # JavaScript no puede leer la cookie
        samesite="lax",  # no se envía en peticiones cross-site
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie(COOKIE_NAME)
    return response


# --- Gestor de entradas -----------------------------------------------------

@router.get("")
def manager(
    request: Request,
    username: str = Depends(require_admin),
    db=Depends(get_db),
    cleaned: int | None = None,  # resultado de /admin/media/cleanup
):
    return templates.TemplateResponse(
        request,
        "admin/manager.html",
        {"posts": posts.list_all(db), "username": username, "cleaned": cleaned},
    )


@router.get("/posts/new")
def new_post_form(request: Request, username: str = Depends(require_admin)):
    return templates.TemplateResponse(request, "admin/form.html", {"post": None})


@router.post("/posts/new")
def create_post(
    username: str = Depends(require_admin),
    db=Depends(get_db),
    title: str = Form(),
    slug: str = Form(""),
    summary: str = Form(""),
    cover_image: str = Form(""),
    content_md: str = Form(""),
    published: bool = Form(False),
    tags_str: str = Form("", alias="tags"),
):
    slug = unique_slug(db, slug or title)
    post = posts.create(
        db, slug, title, summary, cover_image or None,
        content_md, render_markdown(content_md), published,
    )
    _save_tags(db, post["id"], tags_str)
    return RedirectResponse("/admin", status_code=303)


@router.get("/posts/{post_id}/edit")
def edit_post_form(
    request: Request,
    post_id: int,
    username: str = Depends(require_admin),
    db=Depends(get_db),
):
    post = posts.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    tags_str = ", ".join(t["name"] for t in tags.list_for_post(db, post_id))
    return templates.TemplateResponse(
        request, "admin/form.html", {"post": post, "tags_str": tags_str}
    )


@router.post("/posts/{post_id}/edit")
def update_post(
    post_id: int,
    username: str = Depends(require_admin),
    db=Depends(get_db),
    title: str = Form(),
    slug: str = Form(""),
    summary: str = Form(""),
    cover_image: str = Form(""),
    content_md: str = Form(""),
    published: bool = Form(False),
    tags_str: str = Form("", alias="tags"),
):
    if posts.get_by_id(db, post_id) is None:
        raise HTTPException(status_code=404, detail="Post not found")
    slug = unique_slug(db, slug or title, exclude_id=post_id)
    posts.update(
        db, post_id, slug, title, summary, cover_image or None,
        content_md, render_markdown(content_md), published,
    )
    _save_tags(db, post_id, tags_str)
    return RedirectResponse("/admin", status_code=303)


@router.post("/posts/{post_id}/publish")
def toggle_publish(
    post_id: int,
    username: str = Depends(require_admin),
    db=Depends(get_db),
):
    post = posts.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    posts.set_published(db, post_id, not post["published"])
    return RedirectResponse("/admin", status_code=303)


@router.post("/posts/{post_id}/delete")
def delete_post(
    post_id: int,
    username: str = Depends(require_admin),
    db=Depends(get_db),
):
    posts.delete(db, post_id)
    return RedirectResponse("/admin", status_code=303)


@router.post("/media/cleanup")
def cleanup_media(
    username: str = Depends(require_admin),
    db=Depends(get_db),
):
    """Borra de media/ las imágenes que ningún post referencia."""
    deleted = delete_orphans(db)
    return RedirectResponse(f"/admin?cleaned={len(deleted)}", status_code=303)


# --- APIs del editor --------------------------------------------------------

class PreviewIn(BaseModel):
    content_md: str = ""


@router.post("/api/preview")
def preview(data: PreviewIn, username: str = Depends(require_admin)):
    """Renderiza markdown con el MISMO pipeline que al guardar."""
    return {"html": render_markdown(data.content_md)}


ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}


@router.post("/api/images")
def upload_image(file: UploadFile, username: str = Depends(require_admin)):
    """Guarda la imagen en media/ con nombre UUID y devuelve su URL."""
    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported image type")

    name = f"{uuid4().hex}{extension}"
    (Path(settings.media_dir) / name).write_bytes(file.file.read())
    return {"url": f"/media/{name}"}
