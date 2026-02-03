from pydantic import BaseModel, Field


class EarnCoinsRequest(BaseModel):
    user_id: str
    task_type: str | None = Field(default="task_completed")


class SpendCoinsRequest(BaseModel):
    user_id: str
    amount: int
    reason: str


class LogTaskRequest(BaseModel):
    user_id: str
    type: str
    coins_earned: int = 0


class PomodoroCompleteRequest(BaseModel):
    user_id: str
    duration: int = 25


class AIChatRequest(BaseModel):
    user_id: str
    message: str


class BalanceResponse(BaseModel):
    user_id: str
    coins: int
    streak: int
    level: int
    level_progress: int
    next_level_at: int
    theme_unlocked: bool


class WaitlistRequest(BaseModel):
    email: str


class HistoryItem(BaseModel):
    type: str
    coins: int
    timestamp: str


class PomodoroItem(BaseModel):
    duration: int
    coins: int
    completed_at: str


class HistoryResponse(BaseModel):
    tasks: list[HistoryItem]
    pomodoros: list[PomodoroItem]
    streak_calendar: list[dict]
