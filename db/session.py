# DB session generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from core.config import settings 
from contextlib import contextmanager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.DB_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False  # Prevent detached instance errors
)

def get_db() -> Session:
    """Get a database session."""
    logger.info("Creating new database session")
    db = SessionLocal()
    try:
        logger.info("Yielding database session")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise
    finally:
        logger.info("Checking if session should be closed")
        if db.is_active:
            logger.info("Closing active database session")
            db.close()
        else:
            logger.info("Session already closed")

@contextmanager
def get_db_context():
    """Context manager for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
