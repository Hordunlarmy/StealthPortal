from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from portal.engine import create_db
from portal.routes import portal


app = FastAPI()
app.mount("/static", StaticFiles(directory="portal/static"), name="static")
templates = Jinja2Templates(directory="portal/templates")
app.include_router(portal)

create_db()

if __name__ == "__main__":
    uvicorn.run("main:app", reload="True")
