from portal import db
from main import app
from sqlalchemy import text

# Create an application context
with app.app_context():
    db.create_all()
    # db.drop_all()
    # db.session.execute(text('DROP TABLE IF EXISTS message'))
    # db.session.commit()
