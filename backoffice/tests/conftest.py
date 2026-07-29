import os
import tempfile

_DB_FILE = os.path.join(tempfile.gettempdir(), "hbntory_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_FILE}"
os.environ["SESSION_SECRET_KEY"] = "test-secret-key"

import pytest

from app.db import Base, engine, SessionLocal


@pytest.fixture(autouse=True)
def _clean_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
