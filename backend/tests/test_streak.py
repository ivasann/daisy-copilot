from datetime import datetime
from freezegun import freeze_time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend import crud


def make_db():
    engine = create_engine("sqlite+pysqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal


def test_streak_first_activity_no_bonus():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 10:00:00"):
        user = crud.award_coins(db, "u1", 5, "task_completed")
        assert user.streak == 1
        assert user.coins == 5


def test_streak_next_day_bonus():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 10:00:00"):
        crud.award_coins(db, "u1", 5, "task_completed")
    with freeze_time("2026-02-02 09:00:00"):
        user = crud.award_coins(db, "u1", 5, "task_completed")
        assert user.streak == 2
        assert user.coins == 30  # 5 + 5 + 20 bonus


def test_streak_same_day_no_bonus():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 10:00:00"):
        crud.award_coins(db, "u1", 5, "task_completed")
    with freeze_time("2026-02-01 12:00:00"):
        user = crud.award_coins(db, "u1", 5, "task_completed")
        assert user.streak == 1
        assert user.coins == 10


def test_streak_gap_resets():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 10:00:00"):
        crud.award_coins(db, "u1", 5, "task_completed")
    with freeze_time("2026-02-04 10:00:00"):
        user = crud.award_coins(db, "u1", 5, "task_completed")
        assert user.streak == 1
        assert user.coins == 10


def test_spend_coins_insufficient():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 10:00:00"):
        crud.award_coins(db, "u1", 5, "task_completed")
    try:
        crud.spend_coins(db, "u1", 50, "theme_unlock")
    except ValueError as exc:
        assert "Insufficient coins" in str(exc)
    else:
        raise AssertionError("Expected insufficient coins error")


def test_pomodoro_and_task_activity_affects_streak():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 09:00:00"):
        crud.create_pomodoro(db, "u1", 25, 10)
    with freeze_time("2026-02-02 09:00:00"):
        user = crud.create_task(db, "u1", "task_completed", 5)
        assert user.streak == 2
        assert user.coins == 35  # 10 + 5 + 20 bonus


def test_theme_unlock_flag():
    SessionLocal = make_db()
    db = SessionLocal()
    with freeze_time("2026-02-01 09:00:00"):
        user = crud.award_coins(db, "u1", 60, "task_completed")
        assert user.coins == 60
    with freeze_time("2026-02-01 10:00:00"):
        crud.spend_coins(db, "u1", 50, "theme_unlock")
    assert crud.theme_unlocked(db, "u1") is True
