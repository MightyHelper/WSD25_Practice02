"""Tests for the MOTD endpoints (/motd)."""
from fastapi.testclient import TestClient

class TestMOTDEndpoint:
    """Test cases for the MOTD endpoints."""
    
    def test_update_motd(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test updating the MOTD."""
        test_message = "Test MOTD"
        response = test_app.put(
            "/motd",
            json={"message": test_message},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert data["data"]["ok"] is True
        
        # Verify MOTD was updated
        response = test_app.get("/")
        assert response.json()["data"]["last_motd"] == test_message
    
    def test_delete_motd(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test deleting the MOTD."""
        # First set a MOTD
        test_app.put("/motd", json={"message": "To be deleted"}, headers=auth_headers)
        
        # Delete the MOTD
        response = test_app.delete("/motd", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert data["data"]["ok"] is True
        
        # Verify MOTD was deleted
        response = test_app.get("/")
        assert response.json()["data"].get("last_motd") is None
    
    def test_delete_nonexistent_motd(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent MOTD returns 404."""
        # Ensure no MOTD exists
        test_app.delete("/motd", headers=auth_headers)
        
        response = test_app.delete("/motd", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "404"
        assert "not found" in data["title"].lower()
    
    def test_post_motd_not_allowed(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test that POST to /motd is not allowed."""
        response = test_app.post("/motd", json={"message": "test"}, headers=auth_headers)
        assert response.status_code == 405
        data = response.json()
        assert data["status"] == "405"
        assert "Method Not Allowed" in data["title"]
