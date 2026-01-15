"""
Database connection with retry logic for stability.
"""
import os
import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import sessionmaker, scoped_session

# Maximum number of retries for database operations
MAX_RETRIES = 3
# Delay between retries in seconds
RETRY_DELAY = 1.5

def get_db_url():
    """Get the database URL from environment variables."""
    # Check for environment variable first (for production with PostgreSQL)
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return db_url

    # Use SQLite for local development as fallback
    return 'sqlite:///app.db'

def create_db_engine(db_url=None):
    """Create a SQLAlchemy engine with the given URL."""
    if db_url is None:
        db_url = get_db_url()
    
    # Add connection pool settings for better stability
    return create_engine(
        db_url,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,  # Recycle connections after 30 minutes
        pool_pre_ping=True  # Check connection before using
    )

def get_db_session(engine=None):
    """Create a scoped session factory."""
    if engine is None:
        engine = create_db_engine()
    
    session_factory = sessionmaker(bind=engine)
    return scoped_session(session_factory)

def with_retry(func):
    """
    Decorator to retry database operations on connection failure.
    
    Args:
        func: The function to retry
    
    Returns:
        The decorated function with retry logic
    """
    def wrapper(*args, **kwargs):
        retries = 0
        last_error = None
        
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except OperationalError as e:
                if "SSL connection has been closed" in str(e) or "connection has been closed" in str(e):
                    retries += 1
                    last_error = e
                    wait_time = RETRY_DELAY * retries
                    logging.warning(f"Database connection error: {e}. Retrying in {wait_time}s (attempt {retries}/{MAX_RETRIES})")
                    time.sleep(wait_time)
                    
                    # If this is not the last retry, create a new engine
                    if retries < MAX_RETRIES:
                        from models import db
                        from api import app
                        
                        # Create a new engine and update the session
                        engine = create_db_engine()
                        db.get_engine(app).dispose()
                        db.engine = engine
                else:
                    # Other operational errors should be raised immediately
                    raise
            except SQLAlchemyError as e:
                # Other SQLAlchemy errors should be raised immediately
                raise
        
        # If we've exhausted all retries, raise the last error
        if last_error:
            logging.error(f"Database operation failed after {MAX_RETRIES} retries: {last_error}")
            raise last_error
    
    return wrapper