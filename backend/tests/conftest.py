import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.main import app, get_db


def _make_test_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return engine, TestingSessionLocal


def _override_get_db(session_local):
    def _get_db():
        db = session_local()
        try:
            yield db
        finally:
            db.close()

    return _get_db


@pytest.fixture()
def client():
    engine, session_local = _make_test_db()
    app.dependency_overrides[get_db] = _override_get_db(session_local)
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
