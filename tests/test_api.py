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
