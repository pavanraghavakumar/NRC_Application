from __future__ import annotations

import uuid


def test_health_and_correlation(client):
    response = client.get("/api/v1/admin/health", headers={"X-Correlation-Id": str(uuid.uuid4())})
    assert response.status_code == 200
    assert response.headers["X-Correlation-Id"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_resource_crud_and_concurrency(client):
    created = client.post("/api/v1/goals", json={"goal": "1: Safety", "goal_text": "Safety"})
    assert created.status_code == 201
    item = created.json()
    listed = client.get("/api/v1/goals?filter[status_reason]=active")
    assert listed.json()["page"]["total_items"] == 1
    assert client.patch(f"/api/v1/goals/{item['id']}", json={"goal_text": "Updated"}).status_code == 428
    updated = client.patch(f"/api/v1/goals/{item['id']}", headers={"If-Match": '"1"'}, json={"goal_text": "Updated"})
    assert updated.status_code == 200
    assert updated.json()["row_version"] == 2
    conflict = client.patch(f"/api/v1/goals/{item['id']}", headers={"If-Match": '"1"'}, json={"goal_text": "Stale"})
    assert conflict.status_code == 409
    assert conflict.json()["code"] == "CONCURRENCY_CONFLICT"


def test_restricted_creation_for_non_edo(client):
    response = client.post(
        "/api/v1/performance-indicators",
        headers={"X-Dev-Roles": "Quarterly Performance Submitter"},
        json={"indicator_code": "AW-1", "indicator_title": "Restricted", "report_level": "cbj_appr", "agency_wide_support_level": "agency"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "INSUFFICIENT_PRIVILEGE_FOR_FIELD_VALUE"


def test_workflow_guards_and_transition(client):
    created = client.post("/api/v1/performance-indicators", json={"indicator_code": "OR-1", "indicator_title": "Indicator", "report_level": "business_product_line", "agency_wide_support_level": "office"}).json()
    submitted = client.post(f"/api/v1/performance-indicators/{created['id']}/submit", json={})
    assert submitted.status_code == 200
    assert submitted.json()["status_reason"] == "pending_approval"
    invalid = client.post(f"/api/v1/performance-indicators/{created['id']}/submit", json={})
    assert invalid.status_code == 409
    approved = client.post(f"/api/v1/performance-indicators/{created['id']}/approve", json={})
    assert approved.status_code == 200
    assert approved.json()["status_reason"] == "finalized"
    assert approved.json()["state"] == "inactive"


def test_bulk_requires_idempotency_key(client):
    response = client.post("/api/v1/workflow/submit", json={"record_type": "performance_indicator", "ids": [str(uuid.uuid4())]})
    assert response.status_code == 400
    assert response.json()["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_unknown_fields_fail_closed(client):
    response = client.post("/api/v1/goals", json={"goal": "x", "made_up": "bad"})
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_FAILED"

