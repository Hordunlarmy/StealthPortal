from portal import db
from main import app

# Create an application context
with app.app_context():
    db.create_all()
    # db.drop_all()
