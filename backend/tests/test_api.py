def test_balance_level_progress(client):
    res = client.get("/balance/u1")
    assert res.status_code == 200
    data = res.json()
    assert data["coins"] == 0
    assert data["level"] == 0
    assert data["level_progress"] == 0

    res = client.post("/earn-coins", json={"user_id": "u1", "task_type": "task_completed"})
    assert res.status_code == 200
    data = res.json()
    assert data["coins"] == 5
    assert data["level"] == 0
    assert data["level_progress"] == 5


def test_pomodoro_complete_rewards(client):
    res = client.post("/pomodoro-complete", json={"user_id": "u1", "duration": 25})
    assert res.status_code == 200
    data = res.json()
    assert data["coins"] == 10


def test_pomodoro_complete_short_no_reward(client):
    res = client.post("/pomodoro-complete", json={"user_id": "u2", "duration": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["coins"] == 0


def test_spend_coins_insufficient_returns_400(client):
    res = client.post("/spend-coins", json={"user_id": "u3", "amount": 50, "reason": "theme_unlock"})
    assert res.status_code == 400
    assert "Insufficient coins" in res.json()["detail"]


def test_pomodoro_invalid_duration(client):
    res = client.post("/pomodoro-complete", json={"user_id": "u4", "duration": 0})
    assert res.status_code == 400
    assert "Duration must be positive" in res.json()["detail"]


def test_log_task_negative_coins(client):
    res = client.post("/log-task", json={"user_id": "u5", "type": "test", "coins_earned": -1})
    assert res.status_code == 400
    assert "non-negative" in res.json()["detail"]
