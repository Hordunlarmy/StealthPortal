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

base_path_1 = Path("StealthPortal/wif_FastAPI/portal/static")
base_path_2 = Path("portal/static")

if base_path_1.parent.exists():
    stealth.mount(
        "/static", StaticFiles(directory=f"{base_path_1.resolve()}"),
        name="static")
else:
    stealth.mount(
        "/static", StaticFiles(directory=f"{base_path_2.resolve()}"),
        name="static")

stealth.include_router(portal)
stealth.include_router(socket)

create_db()

if __name__ == "__main__":
    uvicorn.run("main:stealth", host="0.0.0.0", reload="True")
