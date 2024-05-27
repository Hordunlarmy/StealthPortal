from portal import db
from main import app
from portal.engine.db_storage import User, Message

# Create an application context
with app.app_context():
    print(User.query.all())
    print(Message.query.all())
