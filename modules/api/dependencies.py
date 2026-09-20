from typing import Generator
from sqlalchemy.orm import Session
from database.connection import SessionLocal

def get_db() -> Generator[Session, None, None]:
    """Dependency to get a database session."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
