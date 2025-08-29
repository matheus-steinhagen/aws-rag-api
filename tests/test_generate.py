import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app

@pytest.mark.asyncio
async def test_generate_with_jwt():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1 Faz login para pegar token
        login_resp = await client.post("v1/auth/login", json={"email": "teste@teste.com"})
        token = login_resp.json()["access_token"]

        # 2 Chama generate com token
        response = await client.post(
            "/v1/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": "Fartura e abundância de prosperidade, sabedoria e amor"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "generated" in data
        assert data["user"]["sub"] == "teste"
        assert "request_id" in data