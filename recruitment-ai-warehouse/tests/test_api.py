"""Kiểm thử API: đăng nhập, RBAC, che dữ liệu, kiểm duyệt AI, chống thiên vị, báo cáo, quản lý người dùng."""
from tests.conftest import login


def test_login_and_me(client, hr):
    assert client.post("/api/auth/login", data={"username": "hr.lan", "password": "sai"}).status_code == 401
    me = client.get("/api/auth/me", headers=hr).json()
    assert me["role"] == "hr" and "pii:read" in me["permissions"]
    assert client.get("/api/applications").status_code == 401


def test_two_roles_see_different_data(client, hr, manager):
    all_apps = client.get("/api/applications", headers=hr, params={"page_size": 500}).json()
    dept_apps = client.get("/api/applications", headers=manager, params={"page_size": 500}).json()
    assert all_apps["total"] == 329
    assert 0 < dept_apps["total"] < all_apps["total"]
    assert {a["position"]["department"] for a in dept_apps["items"]} == {"Khối Dữ liệu & AI"}
    hr_cand = all_apps["items"][0]["candidate"]
    mg_cand = dept_apps["items"][0]["candidate"]
    assert hr_cand["full_name"] and "@" in hr_cand["email"] and "*" not in hr_cand["email"]
    assert mg_cand["full_name"] is None and mg_cand["gender"] is None and mg_cand["date_of_birth"] is None
    assert "***@" in mg_cand["email"] and "*" in mg_cand["phone"]
    # quản lý không xem được hồ sơ phòng ban khác
    other = next(a for a in all_apps["items"] if a["position"]["department"] != "Khối Dữ liệu & AI")
    assert client.get(f"/api/applications/{other['id']}", headers=manager).status_code == 404
    # tìm theo tên bị vô hiệu với quản lý
    name = next(a for a in all_apps["items"] if a["position"]["department"] == "Khối Dữ liệu & AI")["candidate"]["full_name"]
    assert client.get("/api/applications", headers=manager, params={"q": name}).json()["total"] == 0
    d_hr = client.get("/api/analytics/dashboard", headers=hr).json()
    d_mg = client.get("/api/analytics/dashboard", headers=manager).json()
    assert d_mg["kpis"]["total_applications"] < d_hr["kpis"]["total_applications"]


def test_permissions_forbidden_for_manager(client, manager):
    for method, path in [("get", "/api/users"), ("get", "/api/etl/runs"), ("get", "/api/analytics/fairness"),
                         ("post", "/api/ai/rejection-insights"), ("get", "/api/audit-logs")]:
        r = getattr(client, method)(path, headers=manager, **({"json": {}} if method == "post" else {}))
        assert r.status_code == 403, path


def test_dashboard_metrics(client, hr):
    d = client.get("/api/analytics/dashboard", headers=hr).json()
    reached = [f["reached"] for f in d["funnel"]]
    assert reached == sorted(reached, reverse=True)  # phễu giảm dần
    assert d["kpis"]["hired"] == reached[-1]
    assert any(b["type"] == "duration" for b in d["bottlenecks"])
    slow = next(b for b in d["bottlenecks"] if b["type"] == "duration")
    assert slow["stage"] == "HR_INTERVIEW"  # chờ phỏng vấn chuyên môn là điểm nghẽn (đúng như dữ liệu mô phỏng)


def test_ai_insight_review_workflow(client, hr, manager):
    items = client.get("/api/applications", headers=hr, params={"page_size": 500}).json()["items"]
    target = next(a for a in items if a["candidate"]["has_cv"] and a["position"]["department"] == "Khối Dữ liệu & AI")
    ins = client.post(f"/api/ai/applications/{target['id']}/analyze-cv", headers=hr).json()
    assert ins["status"] == "pending_review" and "ho_ten" in ins["removed_fields"]
    assert target["candidate"]["full_name"] not in ins["content"]["anonymized_preview"]
    # Quản lý chưa thấy khi chưa duyệt
    detail = client.get(f"/api/applications/{target['id']}", headers=manager).json()
    assert all(i["id"] != ins["id"] for i in detail["insights"])
    assert client.post(f"/api/ai/insights/{ins['id']}/review", headers=manager, json={"action": "approve"}).status_code == 403
    # HR sửa nội dung có thiên vị → bắt buộc ghi chú
    edited = dict(ins["content"], summary="Ứng viên nữ, phù hợp")
    r = client.post(f"/api/ai/insights/{ins['id']}/review", headers=hr, json={"action": "approve", "edited_content": edited})
    assert r.status_code == 400
    clean = dict(ins["content"], summary="Ứng viên có kinh nghiệm SQL tốt")
    r = client.post(f"/api/ai/insights/{ins['id']}/review", headers=hr, json={"action": "approve", "edited_content": clean})
    assert r.status_code == 200 and r.json()["status"] == "approved" and r.json()["edited"]
    detail = client.get(f"/api/applications/{target['id']}", headers=manager).json()
    assert any(i["id"] == ins["id"] for i in detail["insights"])


def test_interview_questions_and_uploaded_cv(client, hr):
    items = client.get("/api/applications", headers=hr, params={"status": "active"}).json()["items"]
    q = client.post(f"/api/ai/applications/{items[0]['id']}/interview-questions", headers=hr).json()
    assert len(q["content"]["questions"]) >= 5 and q["content"]["avoid_topics"]
    cv = "TRẦN THỊ B\nNgày sinh: 01/01/2000\nKINH NGHIỆM LÀM VIỆC\n- Phát triển API FastAPI cho 5 dịch vụ\nKỸ NĂNG\nPython, FastAPI"
    r = client.post("/api/ai/analyze-cv-file", headers=hr, files={"file": ("cv.txt", cv.encode())})
    assert r.status_code == 200
    assert "FastAPI" in r.json()["content"]["skills"] and "TRẦN THỊ B" not in r.json()["content"]["anonymized_preview"]


def test_decision_blocks_biased_feedback(client, manager):
    items = client.get("/api/applications", headers=manager, params={"status": "active"}).json()["items"]
    app_id = items[0]["id"]
    r = client.post(f"/api/applications/{app_id}/decision", headers=manager,
                    json={"decision": "fail", "feedback": "Ứng viên lớn tuổi so với team", "reason": "Không phù hợp"})
    assert r.status_code == 422 and r.json()["detail"]["bias_flags"]
    r = client.post(f"/api/applications/{app_id}/decision", headers=manager,
                    json={"decision": "pass", "score": 4, "feedback": "Giải tốt bài SQL, trình bày rõ ràng"})
    assert r.status_code == 200
    assert r.json()["current_stage_order"] == items[0]["current_stage_order"] + 1


def test_weekly_report_flow(client, hr, manager):
    rep = client.post("/api/reports/weekly", headers=hr, json={"week_start": "2026-10-26"}).json()
    assert rep["status"] == "draft" and "Báo cáo pipeline tuyển dụng tuần" in rep["narrative"]
    assert all(r["id"] != rep["id"] for r in client.get("/api/reports", headers=manager).json())
    client.post(f"/api/reports/{rep['id']}/approve", headers=hr)
    assert any(r["id"] == rep["id"] for r in client.get("/api/reports", headers=manager).json())
    html = client.get(f"/api/reports/{rep['id']}/download", headers=manager, params={"format": "html"})
    assert html.status_code == 200 and "<table>" in html.text


def test_user_management(client, admin):
    r = client.post("/api/users", headers=admin, json={"username": "manager.sales", "full_name": "QL Kinh doanh",
                                                      "role": "hiring_manager", "department_id": 4,
                                                      "password": "Sales@1234"})
    assert r.status_code == 201
    headers = login(client, "manager.sales", "Sales@1234")
    apps = client.get("/api/applications", headers=headers, params={"page_size": 500}).json()["items"]
    assert apps and {a["position"]["department"] for a in apps} == {"Phòng Kinh doanh"}
    client.patch(f"/api/users/{r.json()['id']}", headers=admin, json={"is_active": False})
    assert client.post("/api/auth/login", data={"username": "manager.sales", "password": "Sales@1234"}).status_code == 403
    logs = client.get("/api/audit-logs", headers=admin).json()
    assert any(l["action"] == "user:create" for l in logs)
