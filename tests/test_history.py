import pytest
from httpx import AsyncClient, ASGITransport

from src.main import app

@pytest.mark.asyncio
async def test_history_returns_items():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1 login
        login_resp = await client.post("/v1/auth/login", json={"email": "teste@teste.com"})
        token = login_resp.json()["access_token"]

        # 2 Gera um prompt (isso vai salvar no Dynamo simulado)
        await client.post(
            "/v1/generate",
            headers={"Authorization": f"Bearer {token}"},
            json={"prompt": "histórico teste"}
        )

        # 3 Consulta o histórico
        history_resp = await client.get(
            "/v1/history",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert history_resp.status_code == 200
        items = history_resp.json()
        assert len(items) > 0
        assert items[0]["prompt"] == "histórico teste"