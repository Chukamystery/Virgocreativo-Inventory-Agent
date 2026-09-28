import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Import models so SQLAlchemy knows about
# every table before create_all() runs.
from app import models


@pytest.fixture()
def test_database(tmp_path):
    """
    Create a completely separate SQLite
    database for each test.

    The database is created inside pytest's
    temporary folder and is removed after
    testing.

    This means our real development database:
        data/inventory_agent.db

    is not used by automated tests.
    """

    database_file = (
        tmp_path
        / "inventory_agent_test.db"
    )

    database_url = (
        f"sqlite:///{database_file}"
    )

    test_engine = create_engine(
        database_url,
        connect_args={
            "check_same_thread": False
        },
    )

    # SQLite does not enforce foreign keys
    # automatically, so enable them for tests.
    @event.listens_for(
        test_engine,
        "connect",
    )
    def enable_foreign_keys(
        dbapi_connection,
        connection_record,
    ):
        cursor = (
            dbapi_connection.cursor()
        )

        cursor.execute(
            "PRAGMA foreign_keys=ON"
        )

        cursor.close()

    TestingSessionLocal = (
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=test_engine,
        )
    )

    Base.metadata.create_all(
        bind=test_engine
    )

    yield {
        "engine":
            test_engine,

        "session_factory":
            TestingSessionLocal,

        "database_file":
            database_file,
    }

    Base.metadata.drop_all(
        bind=test_engine
    )

    test_engine.dispose()

@pytest.fixture()
def db_session(test_database):
    """
    Give individual tests direct access
    to the isolated temporary database.
    """

    TestingSessionLocal = (
        test_database["session_factory"]
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.rollback()
        db.close()

@pytest.fixture()
def client(test_database):
    """
    Create a FastAPI TestClient whose
    database dependency points to the
    temporary pytest database.
    """

    TestingSessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    def override_get_db():

        db = (
            TestingSessionLocal()
        )

        try:
            yield db

        finally:
            db.close()

    app.dependency_overrides[
        get_db
    ] = override_get_db

    with TestClient(
        app
    ) as test_client:

        yield test_client

    app.dependency_overrides.clear()