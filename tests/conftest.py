import pytest
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.main import app
from app.api.deps import get_db
from app.models.base import Base

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Crea las tablas antes de todos los tests y las borra al final.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Entrega una sesión de DB limpia para cada test individual.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """
    Cliente de pruebas síncrono (TestClient de FastAPI usa requests por debajo, 
    pero si tu app es full async quizás necesitemos AsyncClient de httpx).
    Por ahora, TestClient es lo estándar para endpoints básicos.
    """
    with TestClient(app) as c:
        yield c