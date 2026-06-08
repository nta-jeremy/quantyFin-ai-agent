import os
import pytest
from fastapi.testclient import TestClient


class TestConfigSecretValidation:
    def test_empty_postgres_password_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POSTGRES_PASSWORD", "")
        monkeypatch.setenv("NEO4J_PASSWORD", "test")
        monkeypatch.setenv("SECRET_KEY", "test")
        from app.core.config import Settings
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert "POSTGRES_PASSWORD" in str(exc_info.value)

    def test_empty_neo4j_password_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("NEO4J_PASSWORD", "")
        monkeypatch.setenv("SECRET_KEY", "test")
        from app.core.config import Settings
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert "NEO4J_PASSWORD" in str(exc_info.value)

    def test_empty_secret_key_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("NEO4J_PASSWORD", "test")
        monkeypatch.setenv("SECRET_KEY", "")
        from app.core.config import Settings
        with pytest.raises(Exception) as exc_info:
            Settings()
        assert "SECRET_KEY" in str(exc_info.value)

    def test_all_secrets_set_passes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("NEO4J_PASSWORD", "test")
        monkeypatch.setenv("SECRET_KEY", "test")
        from app.core.config import Settings
        s = Settings()
        assert s.POSTGRES_PASSWORD == "test"
        assert s.NEO4J_PASSWORD == "test"
        assert s.SECRET_KEY == "test"


class TestCORSConfiguration:
    def test_cors_not_wildcard(self) -> None:
        from app.core.config import settings
        assert "*" not in settings.CORS_ORIGINS

    def test_cors_origins_contains_localhost(self) -> None:
        from app.core.config import settings
        assert "http://localhost:5173" in settings.CORS_ORIGINS

    def test_cors_middleware_configured(self) -> None:
        from app.main import app
        cors_middleware = None
        for mw in app.user_middleware:
            if "CORSMiddleware" in str(mw.cls):
                cors_middleware = mw
                break
        assert cors_middleware is not None
        origins = cors_middleware.kwargs.get("allow_origins", [])
        assert "*" not in origins


class TestExceptionLeak:
    def test_generic_exception_hides_details(self) -> None:
        from app.main import app

        @app.get("/test-error-route")
        async def trigger_error():
            raise RuntimeError("sensitive internal detail")

        with TestClient(app, raise_server_exceptions=False) as tc:
            response = tc.get("/test-error-route")
            assert response.status_code == 500
            data = response.json()
            assert data["error"]["details"] == "Internal server error"
            assert "sensitive internal detail" not in response.text


class TestSecurityHeaders:
    def test_security_headers_present(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert response.headers.get("Content-Security-Policy") == "default-src 'self'"
        assert response.headers.get("Cache-Control") == "no-store"


class TestRateLimiting:
    def test_rate_limiter_configured(self) -> None:
        from app.main import app
        assert hasattr(app.state, "limiter")
