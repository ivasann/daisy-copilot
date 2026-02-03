from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import Base, SessionLocal, engine
from . import schemas, crud
from .services.llm import chat as llm_chat
from datetime import datetime, timedelta

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Daisy Coin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def build_balance(db: Session, user_id: str):
    user = crud.get_or_create_user(db, user_id)
    level = user.coins // 100
    level_progress = user.coins % 100
    next_level_at = (level + 1) * 100
    return {
        "user_id": user.id,
        "coins": user.coins,
        "streak": user.streak,
        "level": level,
        "level_progress": level_progress,
        "next_level_at": next_level_at,
        "theme_unlocked": crud.theme_unlocked(db, user.id),
    }


@app.get("/balance/{user_id}", response_model=schemas.BalanceResponse)
def get_balance(user_id: str, db: Session = Depends(get_db)):
    return build_balance(db, user_id)


@app.post("/earn-coins", response_model=schemas.BalanceResponse)
def earn_coins(payload: schemas.EarnCoinsRequest, db: Session = Depends(get_db)):
    user = crud.award_coins(db, payload.user_id, 5, payload.task_type or "task_completed")
    return build_balance(db, user.id)


@app.post("/spend-coins", response_model=schemas.BalanceResponse)
def spend_coins(payload: schemas.SpendCoinsRequest, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    if payload.reason == "theme_unlock" and crud.theme_unlocked(db, payload.user_id):
        return build_balance(db, payload.user_id)
    try:
        user = crud.spend_coins(db, payload.user_id, payload.amount, payload.reason)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return build_balance(db, user.id)


@app.post("/log-task", response_model=schemas.BalanceResponse)
def log_task(payload: schemas.LogTaskRequest, db: Session = Depends(get_db)):
    if payload.coins_earned < 0:
        raise HTTPException(status_code=400, detail="coins_earned must be non-negative")
    user = crud.create_task(db, payload.user_id, payload.type, payload.coins_earned)
    return build_balance(db, user.id)


@app.post("/pomodoro-complete", response_model=schemas.BalanceResponse)
def pomodoro_complete(
    payload: schemas.PomodoroCompleteRequest, db: Session = Depends(get_db)
):
    if payload.duration <= 0:
        raise HTTPException(status_code=400, detail="Duration must be positive")
    coins = 10 if payload.duration >= 25 else 0
    user = crud.create_pomodoro(db, payload.user_id, payload.duration, coins)
    return build_balance(db, user.id)


@app.post("/ai-chat")
async def ai_chat(payload: schemas.AIChatRequest, db: Session = Depends(get_db)):
    user = crud.get_or_create_user(db, payload.user_id)
    if user.coins < 1:
        raise HTTPException(status_code=400, detail="Not enough coins for AI chat")
    try:
        reply = await llm_chat(payload.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    try:
        crud.spend_coins(db, payload.user_id, 1, "ai_chat")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {"reply": reply}


@app.post("/waitlist")
def waitlist(payload: schemas.WaitlistRequest, db: Session = Depends(get_db)):
    if "@" not in payload.email or "." not in payload.email:
        raise HTTPException(status_code=400, detail="Invalid email")
    entry = crud.add_waitlist(db, payload.email.lower())
    return {"status": "ok", "email": entry.email}


@app.get("/history/{user_id}", response_model=schemas.HistoryResponse)
def history(user_id: str, db: Session = Depends(get_db)):
    tasks, pomodoros = crud.get_history(db, user_id)
    task_items = [
        {"type": t.type, "coins": t.coins_earned, "timestamp": t.timestamp.isoformat()}
        for t in tasks
    ]
    pomo_items = [
        {"duration": p.duration, "coins": p.coins_earned, "completed_at": p.completed_at.isoformat()}
        for p in pomodoros
    ]

    today = datetime.utcnow().date()
    streak_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        active = any(t.timestamp.date() == day for t in tasks) or any(
            p.completed_at.date() == day for p in pomodoros
        )
        streak_days.append({"date": day.isoformat(), "active": active})

    return {"tasks": task_items, "pomodoros": pomo_items, "streak_calendar": streak_days}
