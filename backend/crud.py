from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import User, Task, PomodoroSession
from .models import Waitlist


def get_or_create_user(db: Session, user_id: str, name: str = "Guest") -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user
    user = User(id=user_id, name=name, coins=0, streak=0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_last_activity_datetime(db: Session, user_id: str):
    last_task = (
        db.query(Task.timestamp)
        .filter(Task.user_id == user_id)
        .order_by(desc(Task.timestamp))
        .first()
    )
    last_pomo = (
        db.query(PomodoroSession.completed_at)
        .filter(PomodoroSession.user_id == user_id)
        .order_by(desc(PomodoroSession.completed_at))
        .first()
    )
    candidates = []
    if last_task:
        candidates.append(last_task[0])
    if last_pomo:
        candidates.append(last_pomo[0])
    return max(candidates) if candidates else None


def apply_streak_and_bonus(db: Session, user: User, activity_time: datetime) -> int:
    last_activity = get_last_activity_datetime(db, user.id)
    today = activity_time.date()
    bonus = 0

    if last_activity is None:
        user.streak = 1
        return bonus

    last_date = last_activity.date()
    if last_date == today:
        return bonus
    if last_date == today - timedelta(days=1):
        user.streak += 1
        bonus = 20
        return bonus

    user.streak = 1
    return bonus


def log_task(db: Session, user: User, task_type: str, coins_earned: int, timestamp: datetime):
    task = Task(
        user_id=user.id,
        type=task_type,
        coins_earned=coins_earned,
        timestamp=timestamp,
    )
    db.add(task)
    return task


def award_coins(db: Session, user_id: str, coins: int, task_type: str):
    user = get_or_create_user(db, user_id)
    now = datetime.utcnow()

    bonus = apply_streak_and_bonus(db, user, now)
    user.coins += coins + bonus

    log_task(db, user, task_type, coins, now)
    if bonus:
        log_task(db, user, "streak_bonus", bonus, now)

    db.commit()
    db.refresh(user)
    return user


def spend_coins(db: Session, user_id: str, amount: int, reason: str):
    user = get_or_create_user(db, user_id)
    if user.coins < amount:
        raise ValueError("Insufficient coins")

    now = datetime.utcnow()
    bonus = apply_streak_and_bonus(db, user, now)
    user.coins = user.coins - amount + bonus

    log_task(db, user, reason, 0, now)
    if bonus:
        log_task(db, user, "streak_bonus", bonus, now)

    db.commit()
    db.refresh(user)
    return user


def create_pomodoro(db: Session, user_id: str, duration: int, coins_earned: int):
    user = get_or_create_user(db, user_id)
    now = datetime.utcnow()

    bonus = apply_streak_and_bonus(db, user, now)
    user.coins += coins_earned + bonus

    session = PomodoroSession(
        user_id=user.id,
        duration=duration,
        coins_earned=coins_earned,
        completed_at=now,
    )
    db.add(session)
    if bonus:
        log_task(db, user, "streak_bonus", bonus, now)

    db.commit()
    db.refresh(user)
    return user


def create_task(db: Session, user_id: str, task_type: str, coins_earned: int):
    user = get_or_create_user(db, user_id)
    now = datetime.utcnow()

    bonus = apply_streak_and_bonus(db, user, now)
    user.coins += coins_earned + bonus
    log_task(db, user, task_type, coins_earned, now)
    if bonus:
        log_task(db, user, "streak_bonus", bonus, now)

    db.commit()
    db.refresh(user)
    return user


def theme_unlocked(db: Session, user_id: str) -> bool:
    return (
        db.query(Task)
        .filter(Task.user_id == user_id, Task.type == "theme_unlock")
        .first()
        is not None
    )


def add_waitlist(db: Session, email: str):
    existing = db.query(Waitlist).filter(Waitlist.email == email).first()
    if existing:
        return existing
    entry = Waitlist(email=email)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_history(db: Session, user_id: str, limit: int = 20):
    tasks = (
        db.query(Task)
        .filter(Task.user_id == user_id)
        .order_by(Task.timestamp.desc())
        .limit(limit)
        .all()
    )
    pomodoros = (
        db.query(PomodoroSession)
        .filter(PomodoroSession.user_id == user_id)
        .order_by(PomodoroSession.completed_at.desc())
        .limit(limit)
        .all()
    )
    return tasks, pomodoros
