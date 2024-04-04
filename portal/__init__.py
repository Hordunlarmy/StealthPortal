from flask import Flask
from .sockets import socketio
from .routes import main, bcrypt
from .engine.db_storage import db, login_manager

rooms = {}


def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config["SECRET_KEY"] = "c0851757a345207ea1e92661138d847b"
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    app.register_blueprint(main)

    socketio.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    return app
