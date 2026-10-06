import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app import models
from app.auth import get_current_user
from app.database import Base, get_db
from app.main import app


# =====================================================
# TEST DATABASE
# =====================================================

@pytest.fixture()
def test_database(tmp_path):
    """
    Create a completely separate SQLite
    database for each test.
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


# =====================================================
# DATABASE SESSION
# =====================================================

@pytest.fixture()
def db_session(test_database):
    """
    Give individual tests direct access
    to the isolated temporary database.
    """

    TestingSessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.rollback()
        db.close()


# =====================================================
# NORMAL / UNAUTHENTICATED CLIENT
# =====================================================

@pytest.fixture()
def client(test_database):
    """
    FastAPI TestClient using the temporary
    test database.

    No authenticated user is supplied here.

    Use this fixture when testing that
    unauthenticated access is rejected.
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


# =====================================================
# AUTHENTICATED TEST USER
# =====================================================

@pytest.fixture()
def authenticated_user(
    test_database,
):
    """
    Create a real business user inside
    the temporary test database.

    This avoids using real Supabase users,
    passwords or access tokens during tests.
    """

    TestingSessionLocal = (
        test_database[
            "session_factory"
        ]
    )

    db = TestingSessionLocal()

    user = models.User(
        full_name=(
            "Authenticated Test Admin"
        ),
        role="ADMIN",
        active=True,
        auth_user_id=(
            "00000000-0000-0000-0000-000000000001"
        ),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Save the values before closing
    # the SQLAlchemy session.
    user_id = user.user_id
    full_name = user.full_name
    role = user.role
    active = user.active
    auth_user_id = user.auth_user_id

    db.close()

    # Return a normal User object representing
    # the authenticated account.
    authenticated = models.User(
        user_id=user_id,
        full_name=full_name,
        role=role,
        active=active,
        auth_user_id=auth_user_id,
    )

    return authenticated


# =====================================================
# AUTHENTICATED CLIENT
# =====================================================

@pytest.fixture()
def authenticated_client(
    test_database,
    authenticated_user,
):
    """
    FastAPI TestClient that behaves as if
    a valid Supabase user has already been
    authenticated.

    Supabase itself is not contacted.
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

    def override_get_current_user():
        return authenticated_user

    app.dependency_overrides[
        get_db
    ] = override_get_db

    app.dependency_overrides[
        get_current_user
    ] = override_get_current_user

    with TestClient(
        app
    ) as test_client:

        yield test_client

    app.dependency_overrides.clear()