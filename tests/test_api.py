import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.database import Base, get_db
from app.main import app

TEST_DB = "sqlite:///./test_api.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def register_and_login(username="alice"):
    client.post("/api/auth/register", json={
        "email": f"{username}@x.com",
        "username": username,
        "password": "secret123",
    })
    r = client.post("/api/auth/login", data={"username": username, "password": "secret123"})
    return r.json()["access_token"]


def test_register_and_me():
    token = register_and_login("bob")
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "bob"


def test_upload_avatar():
    token = register_and_login("avataruser")
    r = client.post(
        "/api/auth/me/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("avatar.png", b"fake-image", "image/png")},
    )
    assert r.status_code == 200
    assert r.json()["avatar_path"].startswith("/static/uploads/avatars/user_")


def test_submit_attempt_flow():
    # admin
    from app.core.security import hash_password
    from app.database import Base, get_db
    from app.models import Task, User
    db = TestingSession()
    db.add(User(email="a@a.com", username="adm", hashed_password=hash_password("p"), is_admin=True))
    task = Task(title="Test", description="d", topic="T", difficulty=1000, answer="42", xp_reward=10)
    db.add(task)
    db.commit()
    db.refresh(task)
    db.close()

    token = register_and_login("eve")
    h = {"Authorization": f"Bearer {token}"}

    # wrong answer
    r = client.post("/api/attempts", json={"task_id": task.id, "answer": "999"}, headers=h)
    assert r.status_code == 201
    assert r.json()["is_correct"] is False

    # correct answer
    r = client.post("/api/attempts", json={"task_id": task.id, "answer": "42"}, headers=h)
    assert r.json()["is_correct"] is True
    assert r.json()["xp_gained"] == 10

    me = client.get("/api/auth/me", headers=h).json()
    assert me["xp"] == 10
    assert me["current_streak"] == 1


def test_checker_normalization():
    from app.services.checker import check_answer
    assert check_answer(" 42 ", "42")
    assert check_answer("3.14", "3,14")
    assert check_answer("HELLO", "hello")
    assert not check_answer("41", "42")


def test_leaderboard_public():
    r = client.get("/api/leaderboard")
    assert r.status_code == 200


def _seed_admin_and_tasks(n=3):
    from app.core.security import hash_password
    from app.models import Task, User
    db = TestingSession()
    db.add(User(email="a@a.com", username="adm", hashed_password=hash_password("p"), is_admin=True))
    ids = []
    for i in range(n):
        t = Task(
            title=f"Test {i}", description=f"d{i}", topic="T",
            difficulty=500 + i * 300, answer=str(i), xp_reward=10,
        )
        db.add(t)
        db.flush()
        ids.append(t.id)
    db.commit()
    db.close()
    return ids


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_list_filters_and_search():
    _seed_admin_and_tasks(3)
    r = client.get("/api/tasks?search=Test")
    assert r.status_code == 200
    assert len(r.json()) == 3
    r = client.get("/api/tasks?difficulty_level=easy")
    assert r.status_code == 200
    assert all(900 > t["difficulty"] >= 500 for t in r.json())


def test_daily_task():
    _seed_admin_and_tasks(3)
    r = client.get("/api/tasks/daily")
    assert r.status_code == 200
    assert "title" in r.json()


def test_leaderboard_and_recommend():
    ids = _seed_admin_and_tasks(3)
    token = register_and_login("rec1")
    h = {"Authorization": f"Bearer {token}"}
    # solve one
    client.post("/api/attempts", json={"task_id": ids[0], "answer": "0"}, headers=h)
    lb = client.get("/api/leaderboard").json()
    assert any(u["username"] == "rec1" for u in lb)
    rec = client.get("/api/recommend", headers=h).json()
    assert all(t["id"] != ids[0] for t in rec)


def test_solved_filter_and_ids():
    ids = _seed_admin_and_tasks(3)
    token = register_and_login("sf1")
    h = {"Authorization": f"Bearer {token}"}
    client.post("/api/attempts", json={"task_id": ids[1], "answer": "1"}, headers=h)
    solved_ids = client.get("/api/tasks/me/solved-ids", headers=h).json()
    assert ids[1] in solved_ids
    r = client.get("/api/tasks?solved=true", headers=h).json()
    assert len(r) == 1 and r[0]["id"] == ids[1]
    r = client.get("/api/tasks?solved=false", headers=h).json()
    assert ids[1] not in [t["id"] for t in r]


def test_change_password():
    token = register_and_login("pw1")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/auth/me/password", json={"old_password": "secret123", "new_password": "newpass1"}, headers=h)
    assert r.status_code == 200
    # old should not work
    r = client.post("/api/auth/login", data={"username": "pw1", "password": "secret123"})
    assert r.status_code == 401
    # new works
    r = client.post("/api/auth/login", data={"username": "pw1", "password": "newpass1"})
    assert r.status_code == 200


def test_change_password_wrong_old():
    token = register_and_login("pw2")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/auth/me/password", json={"old_password": "wrongoldpass", "new_password": "newpass1"}, headers=h)
    assert r.status_code == 400


def test_admin_crud_requires_admin():
    token = register_and_login("userx")
    h = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/tasks", json={
        "title": "T", "description": "d", "topic": "T", "difficulty": 1000, "xp_reward": 5, "answer": "x",
    }, headers=h)
    assert r.status_code == 403


def test_achievements_include_locked():
    token = register_and_login("ach1")
    h = {"Authorization": f"Bearer {token}"}
    # Need achievements seeded
    from app.services.gamification import ensure_achievements_seeded
    db = TestingSession()
    ensure_achievements_seeded(db)
    db.close()
    r = client.get("/api/me/achievements?include_locked=true", headers=h).json()
    assert len(r) > 0
    assert all("unlocked" in a for a in r)
    assert any(not a["unlocked"] for a in r)


def test_404_html_page():
    r = client.get("/this-does-not-exist")
    assert r.status_code == 404
    # Should be HTML, not JSON
    assert "text/html" in r.headers.get("content-type", "")


def test_404_api_returns_json():
    r = client.get("/api/nope")
    assert r.status_code == 404
    assert r.headers.get("content-type", "").startswith("application/json")
