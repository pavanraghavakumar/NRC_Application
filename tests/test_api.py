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


def test_extended_metadata(client):
    assert client.get("/api/v1/metadata/entities/goals/views").json()["items"]
    assert client.get("/api/v1/metadata/entities/goals/forms").json()["items"][0]["tabs"]
    assert client.get("/api/v1/metadata/option-sets/quarter").json()["options"][0]["value"] == "q1"
    assert client.get("/api/v1/metadata/navigation").json()["groups"][-1]["label"] == "Administration"


def test_relationships(client):
    indicator = client.post("/api/v1/performance-indicators", json={"indicator_code": "REL-1", "indicator_title": "Relationship", "report_level": "business_product_line", "agency_wide_support_level": "office"}).json()
    office = client.post("/api/v1/offices", json={"office": "NRR"}).json()
    added = client.post(f"/api/v1/performance-indicators/{indicator['id']}/contributing-offices", json={"ids": [office["id"]]})
    assert added.json()["items"] == [{"id": office["id"]}]
    assert client.delete(f"/api/v1/performance-indicators/{indicator['id']}/contributing-offices/{office['id']}").status_code == 204


def test_audit_and_analytics(client):
    item = client.post("/api/v1/goals", json={"goal": "2: Security", "goal_text": "Secure"}).json()
    client.patch(f"/api/v1/goals/{item['id']}", headers={"If-Match": '"1"'}, json={"goal_text": "Updated"})
    assert client.get(f"/api/v1/goals/{item['id']}/audit").json()["items"]
    analytics = client.get("/api/v1/analytics/strategic-planning-home").json()
    assert analytics["page"] == "strategic-planning-home" and analytics["summary"]["total"] == 1


def test_preferences_jobs_import_export_attachment(client):
    assert client.put("/api/v1/notifications/preferences", json={"in_app": True, "email": False, "teams": False}).json()["email"] is False
    assert client.post("/api/v1/admin/jobs/refresh_analytics/run").json()["status"] == "succeeded"
    assert client.get("/api/v1/admin/jobs", headers={"X-Dev-Roles": "SPA View Only User"}).status_code == 403
    client.post("/api/v1/goals", json={"goal": "3: Trust", "goal_text": "Trust"})
    assert "goal_text" in client.get("/api/v1/goals/export").text
    valid = client.post("/api/v1/import/validate?entity=goals", content=b"goal,goal_text\n4: People,People\n", headers={"Content-Type": "text/csv"})
    assert valid.json() == {"valid": True, "row_count": 1, "errors": []}
    uploaded = client.post("/api/v1/attachments?filename=evidence.txt", content=b"evidence", headers={"Content-Type": "text/plain"}).json()
    assert client.get(f"/api/v1/attachments/{uploaded['id']}/{uploaded['filename']}").content == b"evidence"


def test_visibility_and_idempotency(client):
    owner = "00000000-0000-4000-8000-000000000010"
    owner_headers = {"X-Dev-User-Id": owner, "X-Dev-Roles": "Quarterly Performance Submitter"}
    created = client.post("/api/v1/performance-indicators", headers=owner_headers, json={"indicator_code": "VIS-1", "indicator_title": "Private", "report_level": "business_product_line", "agency_wide_support_level": "office"}).json()
    hidden = client.get(f"/api/v1/performance-indicators/{created['id']}", headers={"X-Dev-User-Id": "00000000-0000-4000-8000-000000000011", "X-Dev-Roles": "Quarterly Performance Submitter"})
    assert hidden.status_code == 404
    payload = {"record_type": "performance_indicator", "ids": [created["id"]]}; headers = {**owner_headers, "Idempotency-Key": "submit-vis"}
    first = client.post("/api/v1/workflow/submit", headers=headers, json=payload)
    replay = client.post("/api/v1/workflow/submit", headers=headers, json=payload)
    assert first.status_code == replay.status_code == 200 and replay.json() == first.json()


def test_analytics_route_order_export_and_query(client):
    refresh = client.get("/api/v1/analytics/refresh-status")
    assert refresh.status_code == 200 and refresh.json()["mode"] == "live"
    exported = client.get("/api/v1/analytics/strategic-planning-home/export")
    assert exported.status_code == 200 and "goal_text" in exported.text
    assert client.get("/api/v1/analytics/query/suggestions").json()["items"]
    query = client.post("/api/v1/analytics/query", json={"question": "How many risks?"})
    assert query.status_code == 200 and query.json()["visual"]["type"] == "table"
    assert client.post("/api/v1/analytics/query", json={"question": ""}).status_code == 400


def test_import_execution_prefill_revision_and_attachment_delete(client):
    imported = client.post("/api/v1/import/jobs?entity=goals", content=b"goal,goal_text\n5: Future,Future\n", headers={"Content-Type": "text/csv"})
    assert imported.status_code == 201 and imported.json()["imported_rows"] == 1
    previous = client.post("/api/v1/performance-indicators", json={"indicator_code": "PREV-1", "indicator_title": "Previous", "report_level": "business_product_line", "agency_wide_support_level": "office"}).json()
    current = client.post("/api/v1/performance-indicators", json={"indicator_code": "CUR-1", "indicator_title": "Current", "report_level": "business_product_line", "agency_wide_support_level": "office"}).json()
    prefill = client.get(f"/api/v1/performance-indicators/{current['id']}/prefill?previous_pi_id={previous['id']}")
    assert prefill.status_code == 200 and prefill.json()["indicator_title"] == "Previous"
    assert len(client.get(f"/api/v1/performance-indicators/{current['id']}/revision-chain").json()["items"]) == 1
    uploaded = client.post("/api/v1/attachments?filename=remove.txt", content=b"remove").json()
    path = f"/api/v1/attachments/{uploaded['id']}/{uploaded['filename']}"
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


def test_option_sets_are_material_and_unsupported_exports_fail(client):
    options = client.get("/api/v1/metadata/option-sets").json()["items"]
    assert len(options) >= 15
    assert client.get("/api/v1/analytics/strategic-planning-home/export?format=pdf").status_code == 400
    assert client.get("/api/v1/analytics/not-installed/export").status_code == 503
