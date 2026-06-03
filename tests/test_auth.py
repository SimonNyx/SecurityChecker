import pytest

@pytest.mark.asyncio
async def test_login_success(client, analyst_user):
    r = await client.post("/api/v1/auth/login", json={"email": "analyst@test.com", "password": "password123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client, analyst_user):
    r = await client.post("/api/v1/auth/login", json={"email": "analyst@test.com", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_login_unknown_email(client):
    r = await client.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "password123"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_no_token(client):
    r = await client.get("/api/v1/assessments")
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_protected_route_invalid_token(client):
    r = await client.get("/api/v1/assessments", headers={"Authorization": "Bearer notavalidtoken"})
    assert r.status_code == 401
