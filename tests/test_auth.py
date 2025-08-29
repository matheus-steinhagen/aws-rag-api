import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app

@pytest.mark.asyncio
async def test_login_returns_jwt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("v1/auth/login", json={"email": "teste@teste.com"})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"