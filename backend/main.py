"""
Run:
    uvicorn main:app --reload
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import random

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Daisy API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# In-memory store (single user)
# ---------------------------
STORE: Dict[str, Any] = {
    "coins": 0,
    "streak": 0,
    "last_active_date": None,  # YYYY-MM-DD
    "coins_today": 0,
    "focus_minutes_today": 0,
    "history": {
        "tasks": [],
        "pomodoros": [],
    },
}


def today_str() -> str:
    return datetime.utcnow().date().isoformat()


def maybe_reset_daily() -> None:
    today = today_str()
    if STORE["last_active_date"] and STORE["last_active_date"] != today:
        STORE["coins_today"] = 0
        STORE["focus_minutes_today"] = 0


def apply_streak(activity_date: str) -> int:
    if not STORE["last_active_date"]:
        STORE["streak"] = 1
        STORE["last_active_date"] = activity_date
        return 0
    if STORE["last_active_date"] == activity_date:
        return 0
    last = datetime.fromisoformat(STORE["last_active_date"]).date()
    current = datetime.fromisoformat(activity_date).date()
    diff_days = (current - last).days
    if diff_days == 1:
        STORE["streak"] += 1
        STORE["last_active_date"] = activity_date
        return 20
    STORE["streak"] = 1
    STORE["last_active_date"] = activity_date
    return 0


def award_coins(amount: int) -> Dict[str, int]:
    maybe_reset_daily()
    activity_date = today_str()
    streak_bonus = apply_streak(activity_date)
    bonus = 5 if random.random() < 0.1 else 0
    total = amount + streak_bonus + bonus
    STORE["coins"] += total
    STORE["coins_today"] += total
    return {"total": total, "bonus": bonus, "streakBonus": streak_bonus}


def level_from_coins(coins: int) -> int:
    return coins // 100


def balance_payload() -> Dict[str, Any]:
    level = level_from_coins(STORE["coins"])
    return {
        "coins": STORE["coins"],
        "streak": STORE["streak"],
        "last_active_date": STORE["last_active_date"],
        "level": level,
        "level_progress": STORE["coins"] % 100,
        "next_level_at": (level + 1) * 100,
        "coins_today": STORE["coins_today"],
        "focus_minutes_today": STORE["focus_minutes_today"],
    }


class TaskCompleteRequest(BaseModel):
    title: Optional[str] = None
    coins: Optional[int] = Field(default=None, ge=0)


class PomodoroCompleteRequest(BaseModel):
    minutes: int = Field(ge=0)


@app.get("/balance")
def get_balance() -> Dict[str, Any]:
    maybe_reset_daily()
    return balance_payload()


@app.post("/task/complete")
def complete_task(payload: TaskCompleteRequest) -> Dict[str, Any]:
    base = payload.coins if payload.coins is not None else 5
    reward = award_coins(base)
    STORE["history"]["tasks"].insert(
        0,
        {
            "type": "task_completed",
            "title": payload.title,
            "coins": base,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
    return {**balance_payload(), "reward": reward}


@app.post("/pomodoro/complete")
def complete_pomodoro(payload: PomodoroCompleteRequest) -> Dict[str, Any]:
    base = (payload.minutes // 5) * 2
    reward = award_coins(base) if base > 0 else {"total": 0, "bonus": 0, "streakBonus": 0}
    STORE["focus_minutes_today"] += payload.minutes
    STORE["history"]["pomodoros"].insert(
        0,
        {
            "duration": payload.minutes,
            "coins": base,
            "completed_at": datetime.utcnow().isoformat(),
        },
    )
    return {**balance_payload(), "reward": reward}


@app.get("/history")
def get_history() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "tasks": STORE["history"]["tasks"],
        "pomodoros": STORE["history"]["pomodoros"],
    }
