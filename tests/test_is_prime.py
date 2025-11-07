"""Tests for the prime number endpoints (/is_prime)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

class TestPrimeEndpoints:
    """Test cases for the prime number endpoints."""
    
    @pytest.mark.parametrize("number,expected", [
        (2, True),
        (3, True),
        (4, False),
        (5, True),
        (17, True),
        (25, False),
        (997, True),  # Large prime
    ])
    def test_check_prime(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str], 
        number: int, 
        expected: bool
    ) -> None:
        """Test checking if a number is prime."""
        response = test_app.post(
            "/is_prime",
            json={"number": number},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "200"
        assert data["data"]["is_prime"] == expected
    
    def test_check_large_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test checking a very large number returns 402 (Payment Required)."""
        large_number = 1001  # Above the limit of 1000
        response = test_app.post(
            "/is_prime",
            json={"number": large_number},
            headers=auth_headers
        )
        assert response.status_code == 402
        data = response.json()
        assert data["status"] == "402"
        assert "payment" in data["title"].lower()
    
    def test_check_negative_number(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test checking a negative number returns 422 (Validation Error)."""
        response = test_app.post(
            "/is_prime",
            json={"number": -7},
            headers=auth_headers
        )
        assert response.status_code == 422
        data = response.json()
        assert data["status"] == "422"
        assert "greater_than" in data["detail_obj"][0]["type"].lower()
    
    def test_get_not_allowed(self, test_app: TestClient) -> None:
        """Test that GET method is not allowed."""
        response = test_app.get("/is_prime?number=7")
        assert response.status_code == 405
        data = response.json()
        assert data["status"] == "405"
        assert "Method Not Allowed" in data["title"]
    
    def test_put_not_implemented(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test that PUT method returns 501 (Not Implemented)."""
        response = test_app.put(
            "/is_prime",
            json={"number": 7},
            headers=auth_headers
        )
        assert response.status_code == 501
        data = response.json()
        assert data["status"] == "501"
        assert "not implemented" in data["data"]["error"].lower()
    
    def test_delete_not_implemented(
        self, 
        test_app: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test that DELETE method returns 501 (Not Implemented)."""
        response = test_app.request(
            "DELETE",
            "/is_prime",
            json={"number": 7},
            headers=auth_headers
        )
        assert response.status_code == 501
        data = response.json()
        assert data["status"] == "501"
        assert "not implemented" in data["data"]["error"].lower()
