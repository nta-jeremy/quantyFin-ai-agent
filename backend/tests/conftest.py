import os
os.environ.setdefault("POSTGRES_PASSWORD", "test_password")
os.environ.setdefault("NEO4J_PASSWORD", "test_password")
os.environ.setdefault("SECRET_KEY", "test_secret_key")

import pytest
from typing import Generator, AsyncGenerator
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.db import get_session

# SQLite in-memory database engine for testing
test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

@pytest.fixture(name="session", scope="function")
def session_fixture() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture(name="client", scope="function")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    # Override get_session dependency in FastAPI
    def override_get_session():
        yield session
        
    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(name="async_client", scope="function")
async def async_client_fixture(session: Session) -> AsyncGenerator[AsyncClient, None]:
    def override_get_session():
        yield session
        
    app.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

# Autouse fixture to mock LiteLLM / LLM APIs globally to prevent token usage
@pytest.fixture(autouse=True)
def mock_llm_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock LiteLLM completion if it is used
    try:
        import litellm
        
        def mock_completion(*args, **kwargs):
            class MockMessage:
                content = "This is a mocked LLM completion response for testing."
                role = "assistant"
                
            class MockChoice:
                message = MockMessage()
                finish_reason = "stop"
                index = 0
                
            class MockResponse:
                id = "mock-id-12345"
                choices = [MockChoice()]
                created = 1670000000
                model = kwargs.get("model", "mock-model")
                object = "chat.completion"
                
            return MockResponse()
            
        monkeypatch.setattr(litellm, "completion", mock_completion)
    except ImportError:
        pass

    # Mock Neo4j driver connection to avoid connecting to a real Neo4j server during pytest
    try:
        from app.core.neo4j import neo4j_manager
        
        class MockSession:
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            def run(self, *args, **kwargs):
                class MockResult:
                    def data(self):
                        return [{"result": 1}]
                return MockResult()
                
        class MockDriver:
            def session(self, *args, **kwargs):
                return MockSession()
            def verify_connectivity(self):
                return True
            def close(self):
                pass
                
        def mock_get_driver():
            return MockDriver()
            
        monkeypatch.setattr(neo4j_manager, "get_driver", mock_get_driver)
    except ImportError:
        pass
