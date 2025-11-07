"""Tests for the special number endpoints (/special_number)."""
from fastapi.testclient import TestClient

class TestSpecialNumberEndpoints:
    """Test cases for the special number endpoints."""
    
    def test_create_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test creating a special number."""
        number = 42
        response = test_app.post(
            "/special_number",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "201"
        assert data["data"]["ok"] is True
        
        # Verify the number was added
        response = test_app.get(f"/special_number?number={number}")
        assert response.status_code == 200
        assert response.json()["data"]["ok"] is True
    
    def test_create_duplicate_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test that creating a duplicate special number returns 409."""
        number = 123
        # First create
        test_app.post("/special_number", json={"number": number}, headers=auth_headers)
        
        # Try to create again
        response = test_app.post(
            "/special_number",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 409
        data = response.json()
        assert data["status"] == "409"
        assert "already exists" in data["detail"]
    
    def test_update_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test updating a special number (idempotent operation)."""
        number = 420
        # First create
        response = test_app.put(
            "/special_number",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 201  # Created
        
        # Update (should be idempotent)
        response = test_app.put(
            "/special_number",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 200  # OK, already exists
    
    def test_delete_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test deleting a special number."""
        number = 555
        # First create
        test_app.post("/special_number", json={"number": number}, headers=auth_headers)
        
        # Delete
        response = test_app.request(
            "DELETE", 
            "/special_number",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert data["data"]["ok"] is True
        
        # Verify deletion
        response = test_app.get(f"/special_number?number={number}")
        assert response.status_code == 404
    
    def test_delete_nonexistent_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent special number returns 404."""
        response = test_app.request(
            "DELETE",
            "/special_number",
            json={"number": 999999},
            headers=auth_headers
        )
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "404"
        assert "not found" in data["title"].lower()
    
    def test_check_special_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test checking if a number is special."""
        number = 42
        # First make it special
        test_app.post("/special_number", json={"number": number}, headers=auth_headers)
        
        # Check
        response = test_app.get(f"/special_number?number={number}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert data["data"]["ok"] is True
    
    def test_check_non_special_number(self, test_app: TestClient) -> None:
        """Test checking a non-special number returns 404."""
        number = 123456  # Assuming this is not special
        response = test_app.get(f"/special_number?number={number}")
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "404"
        assert "not found" in data["title"].lower()
