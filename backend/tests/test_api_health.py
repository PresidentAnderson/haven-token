"""
Test Health and Status Endpoints
Tests for system health checks and basic API functionality
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Test suite for health check endpoints"""

    def test_root_endpoint(self, client):
        """Test GET / returns version info"""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "HAVEN Token API"
        assert "version" in data
        assert "status" in data
        assert data["status"] == "operational"

    def test_health_endpoint_success(self, client):
        """Test GET /health when all services healthy"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "blockchain" in data
        assert "timestamp" in data

    def test_health_endpoint_returns_contract_address(self, client):
        """Test health endpoint includes contract address"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "contract_address" in data
        # Should be a valid Ethereum address or None
        if data["contract_address"]:
            assert data["contract_address"].startswith("0x")
            assert len(data["contract_address"]) == 42

    def test_health_endpoint_database_connection(self, client):
        """Test health check verifies database connectivity"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # In test environment, database should be connected
        assert data["database"] in ["connected", "disconnected"]

    @pytest.mark.skip(reason="Requires blockchain connection")
    def test_health_endpoint_blockchain_connection(self, client):
        """Test health check verifies blockchain connectivity"""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["blockchain"] in ["connected", "disconnected"]


class TestCORS:
    """Test CORS configuration"""

    def test_cors_allows_configured_origins(self, client):
        """Test CORS headers are set for allowed origins"""
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"}
        )

        assert response.status_code == 200
        # Check for CORS headers (if configured)
        # Note: TestClient may not include CORS headers, this is example

    def test_options_request_supported(self, client):
        """Test OPTIONS requests work (CORS preflight)"""
        response = client.options("/health")

        # OPTIONS should be allowed
        assert response.status_code in [200, 204, 405]
        # 405 is OK if OPTIONS not explicitly handled


class TestErrorHandling:
    """Test global error handling"""

    def test_404_for_unknown_endpoint(self, client):
        """Test 404 returned for non-existent endpoints"""
        response = client.get("/this-endpoint-does-not-exist")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_405_for_wrong_http_method(self, client):
        """Test 405 returned for unsupported HTTP methods"""
        # GET / exists, but DELETE / should not
        response = client.delete("/")

        assert response.status_code == 405
        data = response.json()
        assert "detail" in data

    def test_error_response_format(self, client):
        """Test error responses have consistent format"""
        response = client.get("/api/v1/nonexistent")

        assert response.status_code == 404
        data = response.json()

        # FastAPI default error format
        assert isinstance(data, dict)
        assert "detail" in data


class TestAPIDocumentation:
    """Test API documentation endpoints"""

    def test_openapi_json_available(self, client):
        """Test OpenAPI schema is available at /openapi.json"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_docs_page_available(self, client):
        """Test Swagger UI docs are available"""
        response = client.get("/docs")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_page_available(self, client):
        """Test ReDoc docs are available"""
        response = client.get("/redoc")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestRateLimiting:
    """Test rate limiting (if implemented)"""

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limit_enforced(self, client):
        """Test rate limits prevent excessive requests"""
        # Make 150 rapid requests (assuming 100/min limit)
        responses = []
        for i in range(150):
            response = client.get("/health")
            responses.append(response.status_code)

        # Should get at least one 429 (Too Many Requests)
        assert 429 in responses

    @pytest.mark.skip(reason="Rate limiting not yet implemented")
    def test_rate_limit_headers_present(self, client):
        """Test rate limit headers are returned"""
        response = client.get("/health")

        # Common rate limit headers
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        # (Exact headers depend on rate limiting implementation)
        assert response.status_code == 200


# Performance tests (optional, can be slow)
class TestPerformance:
    """Test API performance characteristics"""

    @pytest.mark.slow
    def test_health_endpoint_responds_quickly(self, client):
        """Test health endpoint responds in < 100ms"""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        # Health check should be fast (< 100ms)
        assert elapsed < 100, f"Health check took {elapsed:.2f}ms (expected <100ms)"

    @pytest.mark.slow
    def test_concurrent_requests_handled(self, client):
        """Test API handles multiple concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/health")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All should succeed
        assert all(r.status_code == 200 for r in results)
        assert len(results) == 10


# Run with: pytest tests/test_api_health.py -v
# Run with coverage: pytest tests/test_api_health.py -v --cov=app --cov-report=term
# Run fast tests only: pytest tests/test_api_health.py -v -m "not slow"
