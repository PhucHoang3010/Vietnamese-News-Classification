"""Cấu hình kiểm thử: dùng CSDL riêng (TEST_DATABASE_URL), nạp dữ liệu mẫu một lần."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg://hr_admin:hr_admin_pw@localhost:5432/recruitment_test")
os.environ["AI_PROVIDER"] = "local"
os.environ["SEED_DEMO"] = "true"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402


@pytest.fixture(scope="session")
def client():
    Base.metadata.drop_all(engine)
    from app.main import app

    with TestClient(app) as c:  # lifespan: tạo bảng + seed + ETL dữ liệu mẫu
        yield c


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


def login(client, username, password="Demo@123"):
    r = client.post("/api/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def hr(client):
    return login(client, "hr.lan")


@pytest.fixture(scope="session")
def manager(client):
    return login(client, "manager.data")


@pytest.fixture(scope="session")
def admin(client):
    return login(client, "admin", "Admin@123")
