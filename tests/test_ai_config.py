import pytest
from tests.conftest import login
from app.models.ai_config import AIProviderConfig, AIProvider

@pytest.fixture
async def ai_config(db):
    config = AIProviderConfig(
        provider=AIProvider.OPENWEBUI,
        base_url="http://localhost:3000",
        api_key="",
        model_name="llama3",
        is_active=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

async def test_analyst_cannot_get_ai_config(client, analyst_user, ai_config):
    token = await login(client, "analyst@test.com")
    r = await client.get("/api/v1/ai-config", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

async def test_admin_can_get_ai_config(client, admin_user, ai_config):
    token = await login(client, "admin@test.com")
    r = await client.get("/api/v1/ai-config", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["provider"] == "openwebui"
    assert "api_key" not in r.json()  # api_key not in AIConfigOut schema

async def test_admin_can_update_ai_config(client, admin_user, ai_config):
    token = await login(client, "admin@test.com")
    r = await client.put(
        "/api/v1/ai-config",
        json={"model_name": "gemma2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["model_name"] == "gemma2"
