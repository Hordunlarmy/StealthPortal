from flask import Flask

from .sockets import socketio
from .routes import main

rooms = {}


def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "c0851757a345207ea1e92661138d847b"

    app.register_blueprint(main)

    socketio.init_app(app)

    return app
