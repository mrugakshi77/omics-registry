import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from omics_registry.db.base import Base

TEST_DATABASE_URL = "postgresql+psycopg2://omics:omics@localhost:5432/omics_registry_test"


@pytest.fixture(scope="session")
def test_engine():
    """One engine for the whole test session; creates all tables once up front."""
    engine = create_engine(TEST_DATABASE_URL, future=True)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(test_engine) -> Session:
    """A DB session isolated in a SAVEPOINT that's always rolled back.

    join_transaction_mode="create_savepoint" is SQLAlchemy's built-in
    support for this pattern: the session commits/rolls back freely, like
    real application code does, but every commit only ends a SAVEPOINT --
    SQLAlchemy transparently opens a new one. The outer transaction is
    only ever rolled back once, here in teardown, undoing everything.
    """
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()
