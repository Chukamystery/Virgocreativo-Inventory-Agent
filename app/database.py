from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


# =====================================================
# DATABASE URL
# =====================================================

database_url = settings.database_url


# Some cloud database providers may return:
#
# postgres://...
#
# SQLAlchemy expects:
#
# postgresql://...
#
# This keeps the application compatible with both.
if database_url.startswith("postgres://"):
    database_url = database_url.replace(
        "postgres://",
        "postgresql://",
        1,
    )


# =====================================================
# ENGINE CONFIGURATION
# =====================================================

engine_options = {
    "pool_pre_ping": True,
}


# SQLite needs this because FastAPI can use
# database connections across different threads.
if database_url.startswith("sqlite"):
    engine_options["connect_args"] = {
        "check_same_thread": False
    }


engine = create_engine(
    database_url,
    **engine_options,
)


# =====================================================
# SQLITE-ONLY FOREIGN KEY SUPPORT
# =====================================================

if database_url.startswith("sqlite"):

    @event.listens_for(
        engine,
        "connect",
    )
    def enable_sqlite_foreign_keys(
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


# =====================================================
# DATABASE SESSION
# =====================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()