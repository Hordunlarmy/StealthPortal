from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from .routes import portal


def create_app():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="portal/static"), name="static")
    app.include_router(portal, prefix="/portal")

    return app
