from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

# The engine is the entry point to the database, configured from your .env file
engine = create_engine(settings.DATABASE_URL)

# A session is the handle for all conversations with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# We will inherit from this class to create each of the database models (ORM models)
Base = declarative_base()

def get_db():
    """
    Dependency function to get a database session for each request.
    It ensures the database connection is always closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
