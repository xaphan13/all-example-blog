"""Punto de entrada: instancia FastAPI, monta estáticos y routers."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.database import pool
from app.routers import admin, public
from app.templating import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()
    yield
    pool.close()


app = FastAPI(title="diegolonio.com", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")

app.include_router(public.router)
app.include_router(admin.router)


# Manejador global de errores HTTP: para los 404 (rutas inexistentes o
# recursos no encontrados) renderizamos nuestra página 404.html con el
# diseño del sitio; el resto de códigos se delega al manejador por
# defecto de FastAPI (respuesta JSON estándar).
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return templates.TemplateResponse(request, "404.html", {}, status_code=404)
    return await http_exception_handler(request, exc)
