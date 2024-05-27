from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os

# Define base paths
base_path_1 = Path("./StealthPortal/wif_FastAPI/portal/engine/portal.db")
base_path_2 = Path("./portal/engine/portal.db")

# Check if the directory exists for the first path
if base_path_1.parent.exists():
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{base_path_1.resolve()}"
else:
    # If not, fall back to the second path or create the directory
    os.makedirs(base_path_2.parent, exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{base_path_2.resolve()}"

# Print statements for debugging
print(f"Using database URL: {SQLALCHEMY_DATABASE_URL}")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
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
