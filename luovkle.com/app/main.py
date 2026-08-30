from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles

from app.views.routes import internal_exception, not_found_exception, router

app = FastAPI(openapi_url=None)

app.include_router(router)

app.mount("/static/", StaticFiles(directory="app/static/"), name="static")


@app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
async def internal_exception_handler(request: Request, _: Exception):
    return internal_exception(request, status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.exception_handler(status.HTTP_404_NOT_FOUND)
async def not_found_exception_handler(request: Request, _: Exception):
    return not_found_exception(request, status.HTTP_404_NOT_FOUND)
