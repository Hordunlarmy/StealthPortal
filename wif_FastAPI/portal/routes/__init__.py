from .routes import portal
from fastapi.templating import Jinja2Templates


templates = Jinja2Templates(directory="portal/templates")
