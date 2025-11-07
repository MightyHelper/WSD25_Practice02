"""Tests for the IP endpoint (/my_ip)."""
import pytest
from starlette.testclient import TestClient


class TestMyIPEndpoint:
    """Test cases for the my_ip endpoint."""
    
    def test_get_my_ip(self, test_app: TestClient) -> None:
        """Test getting the client's IP address."""
        response = test_app.get("/my_ip")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "200"
        assert "ip" in data["data"]
        # The IP might be 127.0.0.1 or ::1 for localhost
        assert data["data"]["ip"] in ["testclient"]
    
    @pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
    def test_unsupported_methods(
        self, 
        test_app: TestClient, 
        method: str
    ) -> None:
        """Test that unsupported methods return 405."""
        response = test_app.request(method, "/my_ip")
        assert response.status_code == 405
        data = response.json()
        assert data["status"] == "405"
        assert "Method Not Allowed" in data["title"]
