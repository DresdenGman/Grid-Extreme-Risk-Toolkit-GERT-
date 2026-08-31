"""
Database connection management using SQLAlchemy.
"""

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# Database URL from environment (defaults to SQLite for development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./gert.db"  # SQLite for development, PostgreSQL for production
)

# Create engine with connection pool configuration
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DB_ECHO", "false").lower() == "true",  # Log SQL queries in debug mode
    # Connection pool settings
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),  # Number of connections to maintain
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),  # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "3600")),  # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session.
    
    Usage:
        @router.get("/predictions")
        def get_predictions(db: Session = Depends(get_db)):
            return db.query(PredictionRecord).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables (create if not exist)."""
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions (for non-FastAPI code)."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
