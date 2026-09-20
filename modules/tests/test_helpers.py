from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from database.base import Base


def create_test_engine():
    """
    Create an isolated database engine for tests.
    """
    ...


def create_test_session(
    engine,
) -> Session:
    """
    Create a database session bound to the test engine.
    """
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    return session_factory()


def initialize_test_database(engine) -> None:
    """
    Create all database tables required by tests.
    """
    Base.metadata.create_all(bind=engine)


def cleanup_test_database(engine) -> None:
    """
    Drop all test database tables.
    """
    Base.metadata.drop_all(bind=engine)