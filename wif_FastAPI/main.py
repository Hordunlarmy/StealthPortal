import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
try:
    from ..wif_FastAPI.portal.engine import create_db
    from ..wif_FastAPI.portal.routes import portal
    from ..wif_FastAPI.portal.ws import socket
except ImportError:
    from portal.engine import create_db
    from portal.routes import portal
    from portal.ws import socket


BASE_PATH = Path(__file__).resolve().parent
stealth = FastAPI()
stealth.mount("/static", StaticFiles(directory=BASE_PATH /
              "portal/static"), name="static")
stealth.include_router(portal)
stealth.include_router(socket)

create_db()

if __name__ == "__main__":
    uvicorn.run("main:stealth", host="0.0.0.0", reload="True")
