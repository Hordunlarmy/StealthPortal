from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

database_url = config("database_url")

engine = create_engine(database_url, connect_args={})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db():
    # Create database if it doesnt already exist
    try:
        from StealthPortal.wif_FastAPI.portal.engine import models
    except ImportError:
        from portal.engine import models

    models.Base.metadata.create_all(bind=engine)
