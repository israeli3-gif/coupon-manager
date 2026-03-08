from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# The database file will be created in the current directory
SQLALCHEMY_DATABASE_URL = "sqlite:///./coupons.db"

# Create the SQLAlchemy engine
# "check_same_thread": False is needed only for SQLite in FastAPI
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create a session factory to interact with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for our database models
Base = declarative_base()

# Dependency function to get a database session for our routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()