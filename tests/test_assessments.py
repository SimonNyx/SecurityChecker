import pytest
from tests.conftest import login

async def test_viewer_cannot_submit(client, viewer_user):
    token = await login(client, "viewer@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "Slack"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403

async def test_analyst_can_submit(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "Slack", "review_mode": "standard"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["product_name"] == "Slack"
    assert data["input_type"] == "name"
    assert data["status"] == "pending"

async def test_repo_url_sets_input_type_repo(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "MyTool", "repo_url": "https://github.com/org/repo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["input_type"] == "repo"

async def test_viewer_can_list(client, viewer_user, analyst_user, db):
    from app.models.assessment import Assessment, InputType, AssessmentStatus, ReviewMode
    a = Assessment(
        product_name="TestApp", input_type=InputType.NAME,
        status=AssessmentStatus.COMPLETE, review_mode=ReviewMode.STANDARD,
        submitted_by=analyst_user.id,
    )
    db.add(a)
    await db.commit()

    token = await login(client, "viewer@test.com")
    r = await client.get("/api/v1/assessments", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert any(item["product_name"] == "TestApp" for item in r.json())

async def test_unauthenticated_cannot_list(client):
    r = await client.get("/api/v1/assessments")
    assert r.status_code == 401
