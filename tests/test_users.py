from tests.conftest import login

async def test_analyst_cannot_list_users(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

async def test_admin_can_list_users(client, admin_user, viewer_user):
    token = await login(client, "admin@test.com")
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin@test.com" in emails

async def test_admin_can_create_user(client, admin_user):
    token = await login(client, "admin@test.com")
    r = await client.post(
        "/api/v1/users",
        json={"email": "newuser@test.com", "password": "pass1234", "full_name": "New User", "role": "viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "newuser@test.com"

async def test_admin_can_deactivate_user(client, admin_user, viewer_user):
    token = await login(client, "admin@test.com")
    r = await client.put(
        f"/api/v1/users/{viewer_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False
