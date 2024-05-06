import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from portal.engine import create_db
from portal.routes import portal
from portal.ws import socket


app = FastAPI()
app.mount("/static", StaticFiles(directory="portal/static"), name="static")
templates = Jinja2Templates(directory="portal/templates")
app.include_router(portal)
app.include_router(socket)

create_db()

if __name__ == "__main__":
    uvicorn.run("main:app", reload="True")
