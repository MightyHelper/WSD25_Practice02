"""Tests for the root endpoint (/)."""
import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_get_root(self, test_app: TestClient) -> None:
        """Test GET / returns 200 and welcome message."""
        response = test_app.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert "Hello" in data["data"]
        assert "last_motd" in data["data"]
    
    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_unsupported_methods(
        self, 
        test_app: TestClient, 
        method: str
    ) -> None:
        """Test that unsupported methods return 405."""
        response = test_app.request(method, "/")
        assert response.status_code == 405
        data = response.json()
        assert data["status"] == "405"
        assert "Method Not Allowed" in data["title"]
