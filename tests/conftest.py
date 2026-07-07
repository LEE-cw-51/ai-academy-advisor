import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.session import Base
from app.dependencies.db import get_db
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def db_engine():
    # StaticPool + check_same_thread=False: TestClient의 스레드가
    # 같은 in-memory DB를 공유하기 위해 필요하다.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    factory = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = factory()
    yield session
    session.close()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)
