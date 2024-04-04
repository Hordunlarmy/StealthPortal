from portal import db
from main import app

# Create an application context
with app.app_context():
    # Assuming db is an instance of SQLAlchemy's engine or session
    # Create all tables defined in the database models
    db.create_all()
